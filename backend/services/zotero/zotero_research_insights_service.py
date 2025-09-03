"""
Zotero Research Insights and Gap Analysis Service
Implements topic clustering, theme identification, research gap detection, and trend analysis
"""
import json
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import Counter, defaultdict
import requests
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text
from sklearn.cluster import KMeans, DBSCAN
from sklearn.decomposition import PCA
from sklearn.feature_extraction.text import TfidfVectorizer
import networkx as nx

from core.config import settings
from core.database import get_db
from models.zotero_models import ZoteroItem, ZoteroLibrary, ZoteroConnection

logger = logging.getLogger(__name__)


class ZoteroResearchInsightsService:
    """Service for research insights, gap analysis, and trend detection"""
    
    def __init__(self):
        self.ollama_url = settings.OLLAMA_URL
        self.model = settings.OLLAMA_MODEL
        self.min_cluster_size = 3
        self.max_clusters = 15
        self.trend_window_years = 5
        
    async def analyze_research_landscape(
        self,
        user_id: str,
        library_id: Optional[str] = None,
        analysis_types: List[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze the overall research landscape for a user's library
        
        Args:
            user_id: User ID
            library_id: Optional specific library to analyze
            analysis_types: Types of analysis (topics, trends, gaps, networks)
            
        Returns:
            Comprehensive research landscape analysis
        """
        if analysis_types is None:
            analysis_types = ["topics", "trends", "gaps", "networks"]
            
        try:
            db = next(get_db())
            
            # Get user's items for analysis
            items = await self._get_user_items_for_analysis(db, user_id, library_id)
            
            if len(items) < 5:
                return {
                    "error": "Insufficient items for research landscape analysis (minimum 5 required)",
                    "item_count": len(items)
                }
            
            analysis_results = {
                "user_id": user_id,
                "library_id": library_id,
                "analysis_types": analysis_types,
                "total_items": len(items),
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "results": {}
            }
            
            # Perform requested analyses
            if "topics" in analysis_types:
                analysis_results["results"]["topics"] = await self._analyze_topic_landscape(items)
                
            if "trends" in analysis_types:
                analysis_results["results"]["trends"] = await self._analyze_research_trends(items)
                
            if "gaps" in analysis_types:
                analysis_results["results"]["gaps"] = await self._detect_research_gaps(items)
                
            if "networks" in analysis_types:
                analysis_results["results"]["networks"] = await self._analyze_research_networks(items)
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"Error analyzing research landscape for user {user_id}: {e}")
            raise
    
    async def identify_research_themes(
        self,
        user_id: str,
        library_id: Optional[str] = None,
        clustering_method: str = "kmeans",
        num_themes: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Identify major research themes using topic clustering
        
        Args:
            user_id: User ID
            library_id: Optional specific library
            clustering_method: Clustering algorithm (kmeans, dbscan)
            num_themes: Number of themes to identify (auto if None)
            
        Returns:
            Identified research themes with supporting papers
        """
        try:
            db = next(get_db())
            
            items = await self._get_user_items_for_analysis(db, user_id, library_id)
            
            if len(items) < self.min_cluster_size:
                return {
                    "error": f"Insufficient items for theme identification (minimum {self.min_cluster_size} required)",
                    "item_count": len(items)
                }
            
            # Extract content for clustering
            item_contents = []
            item_metadata = []
            
            for item in items:
                content = self._extract_clustering_content(item)
                if content.strip():
                    item_contents.append(content)
                    item_metadata.append({
                        "item_id": item.id,
                        "title": item.title,
                        "publication_year": item.publication_year,
                        "creators": item.creators,
                        "tags": item.tags
                    })
            
            if len(item_contents) < self.min_cluster_size:
                return {
                    "error": "Insufficient items with content for theme identification",
                    "items_with_content": len(item_contents)
                }
            
            # Perform clustering
            themes = await self._cluster_research_themes(
                item_contents, item_metadata, clustering_method, num_themes
            )
            
            # Generate theme insights
            for theme in themes:
                theme["insights"] = await self._generate_theme_insights(theme)
                theme["research_directions"] = await self._suggest_research_directions(theme)
            
            return {
                "user_id": user_id,
                "library_id": library_id,
                "clustering_method": clustering_method,
                "num_themes": len(themes),
                "total_items_analyzed": len(item_contents),
                "themes": themes,
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error identifying research themes for user {user_id}: {e}")
            raise
    
    async def detect_research_gaps(
        self,
        user_id: str,
        library_id: Optional[str] = None,
        gap_types: List[str] = None
    ) -> Dict[str, Any]:
        """
        Detect gaps in research coverage
        
        Args:
            user_id: User ID
            library_id: Optional specific library
            gap_types: Types of gaps to detect (temporal, topical, methodological)
            
        Returns:
            Identified research gaps with suggestions
        """
        if gap_types is None:
            gap_types = ["temporal", "topical", "methodological"]
            
        try:
            db = next(get_db())
            
            items = await self._get_user_items_for_analysis(db, user_id, library_id)
            
            if len(items) < 10:
                return {
                    "warning": "Limited items for comprehensive gap analysis",
                    "item_count": len(items),
                    "recommendation": "Add more references for better gap detection"
                }
            
            gaps = {
                "user_id": user_id,
                "library_id": library_id,
                "gap_types": gap_types,
                "total_items": len(items),
                "gaps_detected": {},
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
            if "temporal" in gap_types:
                gaps["gaps_detected"]["temporal"] = await self._detect_temporal_gaps(items)
                
            if "topical" in gap_types:
                gaps["gaps_detected"]["topical"] = await self._detect_topical_gaps(items)
                
            if "methodological" in gap_types:
                gaps["gaps_detected"]["methodological"] = await self._detect_methodological_gaps(items)
            
            # Generate gap-filling recommendations
            gaps["recommendations"] = await self._generate_gap_filling_recommendations(gaps["gaps_detected"])
            
            return gaps
            
        except Exception as e:
            logger.error(f"Error detecting research gaps for user {user_id}: {e}")
            raise
    
    async def analyze_research_trends(
        self,
        user_id: str,
        library_id: Optional[str] = None,
        trend_types: List[str] = None,
        time_window_years: int = 5
    ) -> Dict[str, Any]:
        """
        Analyze research trends and emerging directions
        
        Args:
            user_id: User ID
            library_id: Optional specific library
            trend_types: Types of trends (temporal, topical, citation, collaboration)
            time_window_years: Years to analyze for trends
            
        Returns:
            Research trend analysis with predictions
        """
        if trend_types is None:
            trend_types = ["temporal", "topical", "citation", "collaboration"]
            
        try:
            db = next(get_db())
            
            items = await self._get_user_items_for_analysis(db, user_id, library_id)
            
            # Filter items within time window
            current_year = datetime.now().year
            start_year = current_year - time_window_years
            
            recent_items = [
                item for item in items 
                if item.publication_year and item.publication_year >= start_year
            ]
            
            if len(recent_items) < 5:
                return {
                    "warning": f"Limited recent items for trend analysis (found {len(recent_items)})",
                    "recommendation": "Add more recent publications for better trend detection",
                    "time_window": f"{start_year}-{current_year}"
                }
            
            trends = {
                "user_id": user_id,
                "library_id": library_id,
                "trend_types": trend_types,
                "time_window_years": time_window_years,
                "time_range": f"{start_year}-{current_year}",
                "total_items": len(items),
                "recent_items": len(recent_items),
                "trends": {},
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
            if "temporal" in trend_types:
                trends["trends"]["temporal"] = await self._analyze_temporal_trends(recent_items)
                
            if "topical" in trend_types:
                trends["trends"]["topical"] = await self._analyze_topical_trends(recent_items)
                
            if "citation" in trend_types:
                trends["trends"]["citation"] = await self._analyze_citation_trends(recent_items)
                
            if "collaboration" in trend_types:
                trends["trends"]["collaboration"] = await self._analyze_collaboration_trends(recent_items)
            
            # Generate trend predictions
            trends["predictions"] = await self._generate_trend_predictions(trends["trends"])
            
            return trends
            
        except Exception as e:
            logger.error(f"Error analyzing research trends for user {user_id}: {e}")
            raise
    
    async def _analyze_topic_landscape(self, items: List[ZoteroItem]) -> Dict[str, Any]:
        """Analyze the overall topic landscape"""
        try:
            # Extract topics from all items
            all_topics = []
            topic_years = defaultdict(list)
            topic_items = defaultdict(list)
            
            for item in items:
                # Get AI analysis results if available
                if item.item_metadata and "ai_analysis" in item.item_metadata:
                    analysis = item.item_metadata["ai_analysis"].get("results", {})
                    topics_data = analysis.get("topics", {})
                    
                    primary_topics = topics_data.get("primary_topics", [])
                    for topic in primary_topics:
                        all_topics.append(topic)
                        if item.publication_year:
                            topic_years[topic].append(item.publication_year)
                        topic_items[topic].append({
                            "item_id": item.id,
                            "title": item.title,
                            "year": item.publication_year
                        })
            
            # Count topic frequencies
            topic_counts = Counter(all_topics)
            
            # Calculate topic evolution
            topic_evolution = {}
            for topic, years in topic_years.items():
                if len(years) > 1:
                    years.sort()
                    topic_evolution[topic] = {
                        "first_appearance": min(years),
                        "latest_appearance": max(years),
                        "frequency_over_time": self._calculate_frequency_over_time(years),
                        "trend": "increasing" if years[-1] > years[0] else "stable"
                    }
            
            return {
                "total_topics": len(topic_counts),
                "most_common_topics": topic_counts.most_common(10),
                "topic_distribution": dict(topic_counts),
                "topic_evolution": topic_evolution,
                "coverage_analysis": {
                    "items_with_topics": len([item for item in items if self._has_topic_analysis(item)]),
                    "coverage_percentage": round(
                        len([item for item in items if self._has_topic_analysis(item)]) / len(items) * 100, 2
                    )
                }
            }
            
        except Exception as e:
            logger.warning(f"Error analyzing topic landscape: {e}")
            return {"error": "Failed to analyze topic landscape"}
    
    async def _analyze_research_trends(self, items: List[ZoteroItem]) -> Dict[str, Any]:
        """Analyze research trends over time"""
        try:
            # Group items by year
            items_by_year = defaultdict(list)
            for item in items:
                if item.publication_year:
                    items_by_year[item.publication_year].append(item)
            
            if not items_by_year:
                return {"error": "No items with publication years for trend analysis"}
            
            years = sorted(items_by_year.keys())
            
            # Analyze publication trends
            publication_trend = {
                "years": years,
                "counts": [len(items_by_year[year]) for year in years],
                "trend_direction": self._calculate_trend_direction(
                    [len(items_by_year[year]) for year in years]
                )
            }
            
            # Analyze topic trends
            topic_trends = {}
            for year in years:
                year_topics = []
                for item in items_by_year[year]:
                    if self._has_topic_analysis(item):
                        analysis = item.item_metadata["ai_analysis"]["results"]["topics"]
                        year_topics.extend(analysis.get("primary_topics", []))
                
                if year_topics:
                    topic_trends[year] = Counter(year_topics).most_common(5)
            
            # Identify emerging topics
            emerging_topics = self._identify_emerging_topics(topic_trends, years)
            
            return {
                "publication_trends": publication_trend,
                "topic_trends_by_year": topic_trends,
                "emerging_topics": emerging_topics,
                "time_span": f"{min(years)}-{max(years)}",
                "total_years": len(years)
            }
            
        except Exception as e:
            logger.warning(f"Error analyzing research trends: {e}")
            return {"error": "Failed to analyze research trends"}
    
    async def _detect_research_gaps(self, items: List[ZoteroItem]) -> Dict[str, Any]:
        """Detect gaps in research coverage"""
        try:
            # Analyze temporal gaps
            years = [item.publication_year for item in items if item.publication_year]
            temporal_gaps = self._find_temporal_gaps(years)
            
            # Analyze topical gaps
            all_topics = []
            for item in items:
                if self._has_topic_analysis(item):
                    analysis = item.item_metadata["ai_analysis"]["results"]["topics"]
                    all_topics.extend(analysis.get("primary_topics", []))
            
            topic_coverage = Counter(all_topics)
            underrepresented_topics = [
                topic for topic, count in topic_coverage.items() 
                if count == 1  # Topics with only one paper
            ]
            
            # Analyze methodological gaps
            methodologies = []
            for item in items:
                if self._has_topic_analysis(item):
                    analysis = item.item_metadata["ai_analysis"]["results"]["topics"]
                    methodology = analysis.get("methodology")
                    if methodology:
                        methodologies.append(methodology)
            
            methodology_coverage = Counter(methodologies)
            
            return {
                "temporal_gaps": temporal_gaps,
                "underrepresented_topics": underrepresented_topics[:10],
                "methodology_gaps": {
                    "covered_methodologies": list(methodology_coverage.keys()),
                    "methodology_distribution": dict(methodology_coverage),
                    "suggestions": self._suggest_missing_methodologies(methodology_coverage)
                },
                "coverage_analysis": {
                    "topic_diversity": len(topic_coverage),
                    "methodology_diversity": len(methodology_coverage),
                    "temporal_span": max(years) - min(years) if years else 0
                }
            }
            
        except Exception as e:
            logger.warning(f"Error detecting research gaps: {e}")
            return {"error": "Failed to detect research gaps"}
    
    async def _analyze_research_networks(self, items: List[ZoteroItem]) -> Dict[str, Any]:
        """Analyze research networks and connections"""
        try:
            # Build author collaboration network
            author_network = self._build_author_network(items)
            
            # Build topic co-occurrence network
            topic_network = self._build_topic_network(items)
            
            # Analyze citation patterns (simplified)
            citation_patterns = self._analyze_citation_patterns(items)
            
            return {
                "author_network": author_network,
                "topic_network": topic_network,
                "citation_patterns": citation_patterns,
                "network_metrics": {
                    "total_authors": len(author_network.get("nodes", [])),
                    "total_topics": len(topic_network.get("nodes", [])),
                    "collaboration_density": author_network.get("density", 0)
                }
            }
            
        except Exception as e:
            logger.warning(f"Error analyzing research networks: {e}")
            return {"error": "Failed to analyze research networks"}
    
    async def _cluster_research_themes(
        self,
        contents: List[str],
        metadata: List[Dict[str, Any]],
        method: str,
        num_themes: Optional[int]
    ) -> List[Dict[str, Any]]:
        """Cluster research themes using ML algorithms"""
        try:
            # Create TF-IDF vectors
            vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2),
                min_df=2
            )
            
            tfidf_matrix = vectorizer.fit_transform(contents)
            feature_names = vectorizer.get_feature_names_out()
            
            # Determine number of clusters
            if num_themes is None:
                num_themes = min(max(2, len(contents) // 5), self.max_clusters)
            
            # Perform clustering
            if method == "kmeans":
                clusterer = KMeans(n_clusters=num_themes, random_state=42, n_init=10)
                cluster_labels = clusterer.fit_predict(tfidf_matrix.toarray())
            elif method == "dbscan":
                clusterer = DBSCAN(eps=0.5, min_samples=2)
                cluster_labels = clusterer.fit_predict(tfidf_matrix.toarray())
                num_themes = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
            else:
                raise ValueError(f"Unsupported clustering method: {method}")
            
            # Organize themes
            themes = []
            for cluster_id in range(num_themes):
                cluster_indices = [i for i, label in enumerate(cluster_labels) if label == cluster_id]
                
                if not cluster_indices:
                    continue
                
                # Get cluster items
                cluster_items = [metadata[i] for i in cluster_indices]
                cluster_contents = [contents[i] for i in cluster_indices]
                
                # Extract theme keywords
                cluster_tfidf = tfidf_matrix[cluster_indices]
                mean_tfidf = np.mean(cluster_tfidf.toarray(), axis=0)
                top_indices = np.argsort(mean_tfidf)[-10:][::-1]
                theme_keywords = [feature_names[i] for i in top_indices]
                
                # Generate theme summary
                theme_summary = await self._generate_theme_summary(cluster_contents, theme_keywords)
                
                themes.append({
                    "theme_id": f"theme_{cluster_id}",
                    "theme_name": theme_keywords[0].title() if theme_keywords else f"Theme {cluster_id + 1}",
                    "keywords": theme_keywords,
                    "summary": theme_summary,
                    "item_count": len(cluster_items),
                    "items": cluster_items,
                    "coherence_score": self._calculate_theme_coherence(cluster_tfidf)
                })
            
            return themes
            
        except Exception as e:
            logger.error(f"Error clustering research themes: {e}")
            return []
    
    async def _generate_theme_summary(self, contents: List[str], keywords: List[str]) -> str:
        """Generate AI summary for a research theme"""
        try:
            # Combine contents for analysis
            combined_content = " ".join(contents[:3])  # Limit content length
            keywords_str = ", ".join(keywords[:5])
            
            prompt = f"""
            Analyze this research theme and provide a concise summary.
            
            Key terms: {keywords_str}
            
            Sample content: {combined_content[:1000]}
            
            Provide a 2-3 sentence summary of what this research theme is about,
            focusing on the main concepts, methods, and applications.
            """
            
            response = await self._call_llm(prompt)
            return response.strip() if response else f"Research theme focused on {keywords_str}"
            
        except Exception as e:
            logger.warning(f"Error generating theme summary: {e}")
            return f"Research theme involving {', '.join(keywords[:3])}"
    
    async def _call_llm(self, prompt: str) -> str:
        """Call the LLM with the given prompt"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 512
                    }
                },
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "")
            
        except Exception as e:
            logger.warning(f"Error calling LLM: {e}")
            return ""
    
    def _extract_clustering_content(self, item: ZoteroItem) -> str:
        """Extract content for clustering analysis"""
        content_parts = []
        
        if item.title:
            content_parts.append(item.title)
        
        if item.abstract_note:
            content_parts.append(item.abstract_note)
        
        if item.tags:
            content_parts.extend(item.tags)
        
        return " ".join(content_parts)
    
    def _has_topic_analysis(self, item: ZoteroItem) -> bool:
        """Check if item has AI topic analysis"""
        return (
            item.item_metadata and 
            "ai_analysis" in item.item_metadata and
            "results" in item.item_metadata["ai_analysis"] and
            "topics" in item.item_metadata["ai_analysis"]["results"]
        )
    
    def _calculate_frequency_over_time(self, years: List[int]) -> Dict[str, Any]:
        """Calculate how topic frequency changes over time"""
        year_counts = Counter(years)
        sorted_years = sorted(year_counts.keys())
        
        return {
            "year_counts": dict(year_counts),
            "trend": "increasing" if len(sorted_years) > 1 and year_counts[sorted_years[-1]] > year_counts[sorted_years[0]] else "stable"
        }
    
    def _calculate_trend_direction(self, values: List[int]) -> str:
        """Calculate overall trend direction"""
        if len(values) < 2:
            return "insufficient_data"
        
        # Simple linear trend
        increases = sum(1 for i in range(1, len(values)) if values[i] > values[i-1])
        decreases = sum(1 for i in range(1, len(values)) if values[i] < values[i-1])
        
        if increases > decreases:
            return "increasing"
        elif decreases > increases:
            return "decreasing"
        else:
            return "stable"
    
    def _identify_emerging_topics(self, topic_trends: Dict[int, List[Tuple[str, int]]], years: List[int]) -> List[str]:
        """Identify topics that are becoming more prominent"""
        if len(years) < 3:
            return []
        
        recent_years = years[-3:]  # Last 3 years
        early_years = years[:-3] if len(years) > 3 else []
        
        recent_topics = set()
        for year in recent_years:
            if year in topic_trends:
                recent_topics.update([topic for topic, count in topic_trends[year]])
        
        early_topics = set()
        for year in early_years:
            if year in topic_trends:
                early_topics.update([topic for topic, count in topic_trends[year]])
        
        # Topics that appear in recent years but not in early years
        emerging = list(recent_topics - early_topics)
        return emerging[:5]  # Top 5 emerging topics
    
    def _find_temporal_gaps(self, years: List[int]) -> List[Dict[str, Any]]:
        """Find gaps in temporal coverage"""
        if not years:
            return []
        
        years = sorted(set(years))
        gaps = []
        
        for i in range(len(years) - 1):
            gap_size = years[i + 1] - years[i] - 1
            if gap_size > 2:  # Gap of more than 2 years
                gaps.append({
                    "start_year": years[i],
                    "end_year": years[i + 1],
                    "gap_size": gap_size,
                    "missing_years": list(range(years[i] + 1, years[i + 1]))
                })
        
        return gaps
    
    def _suggest_missing_methodologies(self, methodology_coverage: Counter) -> List[str]:
        """Suggest methodologies that might be missing"""
        common_methodologies = [
            "experimental", "survey", "case study", "systematic review",
            "meta-analysis", "qualitative", "quantitative", "mixed methods",
            "longitudinal", "cross-sectional", "ethnographic", "comparative"
        ]
        
        covered = set(methodology_coverage.keys())
        missing = [method for method in common_methodologies if method not in covered]
        
        return missing[:5]  # Top 5 suggestions
    
    def _build_author_network(self, items: List[ZoteroItem]) -> Dict[str, Any]:
        """Build author collaboration network"""
        try:
            # Extract author collaborations
            collaborations = []
            all_authors = set()
            
            for item in items:
                if item.creators:
                    authors = []
                    for creator in item.creators:
                        if isinstance(creator, dict) and creator.get("creatorType") == "author":
                            name = f"{creator.get('firstName', '')} {creator.get('lastName', '')}".strip()
                            if name:
                                authors.append(name)
                                all_authors.add(name)
                    
                    # Add collaborations (all pairs of authors on same paper)
                    for i in range(len(authors)):
                        for j in range(i + 1, len(authors)):
                            collaborations.append((authors[i], authors[j]))
            
            # Build network structure
            nodes = [{"id": author, "label": author} for author in all_authors]
            edges = []
            collaboration_counts = Counter(collaborations)
            
            for (author1, author2), count in collaboration_counts.items():
                edges.append({
                    "source": author1,
                    "target": author2,
                    "weight": count
                })
            
            return {
                "nodes": nodes,
                "edges": edges,
                "total_collaborations": len(collaborations),
                "unique_collaborations": len(collaboration_counts),
                "density": len(edges) / (len(nodes) * (len(nodes) - 1) / 2) if len(nodes) > 1 else 0
            }
            
        except Exception as e:
            logger.warning(f"Error building author network: {e}")
            return {"nodes": [], "edges": [], "total_collaborations": 0}
    
    def _build_topic_network(self, items: List[ZoteroItem]) -> Dict[str, Any]:
        """Build topic co-occurrence network"""
        try:
            # Extract topic co-occurrences
            topic_pairs = []
            all_topics = set()
            
            for item in items:
                if self._has_topic_analysis(item):
                    analysis = item.item_metadata["ai_analysis"]["results"]["topics"]
                    topics = analysis.get("primary_topics", [])
                    
                    for topic in topics:
                        all_topics.add(topic)
                    
                    # Add topic co-occurrences
                    for i in range(len(topics)):
                        for j in range(i + 1, len(topics)):
                            topic_pairs.append((topics[i], topics[j]))
            
            # Build network structure
            nodes = [{"id": topic, "label": topic} for topic in all_topics]
            edges = []
            cooccurrence_counts = Counter(topic_pairs)
            
            for (topic1, topic2), count in cooccurrence_counts.items():
                if count > 1:  # Only include topics that co-occur multiple times
                    edges.append({
                        "source": topic1,
                        "target": topic2,
                        "weight": count
                    })
            
            return {
                "nodes": nodes,
                "edges": edges,
                "total_cooccurrences": len(topic_pairs),
                "significant_connections": len(edges)
            }
            
        except Exception as e:
            logger.warning(f"Error building topic network: {e}")
            return {"nodes": [], "edges": [], "total_cooccurrences": 0}
    
    def _analyze_citation_patterns(self, items: List[ZoteroItem]) -> Dict[str, Any]:
        """Analyze citation patterns (simplified)"""
        try:
            # Analyze publication venues
            venues = [item.publication_title for item in items if item.publication_title]
            venue_counts = Counter(venues)
            
            # Analyze publication years
            years = [item.publication_year for item in items if item.publication_year]
            year_counts = Counter(years)
            
            return {
                "top_venues": venue_counts.most_common(10),
                "publication_timeline": dict(year_counts),
                "venue_diversity": len(venue_counts),
                "temporal_span": max(years) - min(years) if years else 0
            }
            
        except Exception as e:
            logger.warning(f"Error analyzing citation patterns: {e}")
            return {"top_venues": [], "publication_timeline": {}}
    
    def _calculate_theme_coherence(self, cluster_tfidf) -> float:
        """Calculate coherence score for a theme cluster"""
        try:
            # Simple coherence based on average pairwise similarity
            if cluster_tfidf.shape[0] < 2:
                return 1.0
            
            similarities = []
            for i in range(cluster_tfidf.shape[0]):
                for j in range(i + 1, cluster_tfidf.shape[0]):
                    sim = np.dot(cluster_tfidf[i].toarray().flatten(), 
                               cluster_tfidf[j].toarray().flatten())
                    similarities.append(sim)
            
            return float(np.mean(similarities)) if similarities else 0.0
            
        except Exception as e:
            logger.warning(f"Error calculating theme coherence: {e}")
            return 0.0
    
    async def _get_user_items_for_analysis(
        self,
        db: Session,
        user_id: str,
        library_id: Optional[str] = None
    ) -> List[ZoteroItem]:
        """Get user's items for analysis"""
        query = db.query(ZoteroItem).join(
            ZoteroLibrary, ZoteroItem.library_id == ZoteroLibrary.id
        ).join(
            ZoteroConnection, ZoteroLibrary.connection_id == ZoteroConnection.id
        ).filter(
            and_(
                ZoteroConnection.user_id == user_id,
                ZoteroItem.is_deleted == False
            )
        )
        
        if library_id:
            query = query.filter(ZoteroLibrary.id == library_id)
        
        return query.all()
    
    # Advanced gap detection and trend analysis methods
    async def _detect_temporal_gaps(self, items: List[ZoteroItem]) -> Dict[str, Any]:
        """Detect temporal gaps in research coverage"""
        try:
            years = [item.publication_year for item in items if item.publication_year]
            
            if not years:
                return {
                    "error": "No publication years available for temporal gap analysis",
                    "gaps": []
                }
            
            years = sorted(set(years))
            current_year = datetime.now().year
            
            # Find gaps in publication timeline
            gaps = []
            for i in range(len(years) - 1):
                gap_size = years[i + 1] - years[i] - 1
                if gap_size > 1:  # Gap of more than 1 year
                    gaps.append({
                        "type": "publication_gap",
                        "start_year": years[i],
                        "end_year": years[i + 1],
                        "gap_size": gap_size,
                        "missing_years": list(range(years[i] + 1, years[i + 1])),
                        "severity": "high" if gap_size > 3 else "medium"
                    })
            
            # Check for recent publication gaps
            if years and current_year - max(years) > 2:
                gaps.append({
                    "type": "recent_gap",
                    "last_publication": max(years),
                    "current_year": current_year,
                    "gap_size": current_year - max(years),
                    "severity": "high" if current_year - max(years) > 5 else "medium",
                    "recommendation": "Consider adding more recent publications"
                })
            
            # Analyze publication frequency patterns
            year_counts = Counter(years)
            avg_publications = sum(year_counts.values()) / len(year_counts) if year_counts else 0
            
            low_activity_years = [
                year for year, count in year_counts.items() 
                if count < avg_publications * 0.5 and count > 0
            ]
            
            return {
                "gaps": gaps,
                "analysis": {
                    "total_years_covered": len(years),
                    "year_range": f"{min(years)}-{max(years)}" if years else "N/A",
                    "average_publications_per_year": round(avg_publications, 2),
                    "low_activity_years": low_activity_years,
                    "coverage_density": len([y for y in range(min(years), max(years) + 1) if y in years]) / (max(years) - min(years) + 1) if len(years) > 1 else 1.0
                },
                "recommendations": [
                    f"Fill gaps in years: {gap['missing_years']}" for gap in gaps if gap["type"] == "publication_gap"
                ]
            }
            
        except Exception as e:
            logger.warning(f"Error detecting temporal gaps: {e}")
            return {"error": "Failed to detect temporal gaps", "gaps": []}
    
    async def _detect_topical_gaps(self, items: List[ZoteroItem]) -> Dict[str, Any]:
        """Detect topical gaps in research coverage"""
        try:
            # Extract all topics from items with AI analysis
            all_topics = []
            topic_item_map = defaultdict(list)
            
            for item in items:
                if self._has_topic_analysis(item):
                    analysis = item.item_metadata["ai_analysis"]["results"]["topics"]
                    primary_topics = analysis.get("primary_topics", [])
                    
                    for topic in primary_topics:
                        all_topics.append(topic.lower())
                        topic_item_map[topic.lower()].append(item.id)
            
            if not all_topics:
                return {
                    "error": "No topic analysis available for gap detection",
                    "gaps": []
                }
            
            topic_counts = Counter(all_topics)
            total_topics = len(topic_counts)
            
            # Identify underrepresented topics (topics with only 1-2 papers)
            underrepresented = [
                {
                    "topic": topic,
                    "count": count,
                    "percentage": round(count / len(items) * 100, 2),
                    "severity": "high" if count == 1 else "medium",
                    "recommendation": f"Consider adding more research on {topic}"
                }
                for topic, count in topic_counts.items() 
                if count <= 2
            ]
            
            # Identify topic clusters and potential gaps between them
            topic_relationships = await self._analyze_topic_relationships(all_topics, topic_item_map)
            
            # Suggest related topics that might be missing
            missing_topics = await self._suggest_missing_topics(list(topic_counts.keys()))
            
            return {
                "gaps": {
                    "underrepresented_topics": underrepresented[:10],  # Top 10 underrepresented
                    "topic_isolation": topic_relationships.get("isolated_topics", []),
                    "missing_connections": topic_relationships.get("missing_connections", [])
                },
                "analysis": {
                    "total_unique_topics": total_topics,
                    "topic_diversity_score": total_topics / len(items) if items else 0,
                    "most_common_topics": topic_counts.most_common(5),
                    "topic_distribution": {
                        "well_covered": len([t for t, c in topic_counts.items() if c >= 5]),
                        "moderately_covered": len([t for t, c in topic_counts.items() if 2 < c < 5]),
                        "underrepresented": len([t for t, c in topic_counts.items() if c <= 2])
                    }
                },
                "suggestions": {
                    "missing_topics": missing_topics,
                    "expansion_opportunities": [
                        f"Expand research on {topic} (currently {count} papers)"
                        for topic, count in topic_counts.most_common(3)
                    ]
                }
            }
            
        except Exception as e:
            logger.warning(f"Error detecting topical gaps: {e}")
            return {"error": "Failed to detect topical gaps", "gaps": []}
    
    async def _detect_methodological_gaps(self, items: List[ZoteroItem]) -> Dict[str, Any]:
        """Detect methodological gaps in research coverage"""
        try:
            methodologies = []
            methodology_years = defaultdict(list)
            methodology_topics = defaultdict(set)
            
            for item in items:
                if self._has_topic_analysis(item):
                    analysis = item.item_metadata["ai_analysis"]["results"]["topics"]
                    methodology = analysis.get("methodology")
                    
                    if methodology:
                        methodologies.append(methodology.lower())
                        if item.publication_year:
                            methodology_years[methodology.lower()].append(item.publication_year)
                        
                        # Associate methodology with topics
                        primary_topics = analysis.get("primary_topics", [])
                        for topic in primary_topics:
                            methodology_topics[methodology.lower()].add(topic.lower())
            
            if not methodologies:
                return {
                    "error": "No methodology information available for gap analysis",
                    "gaps": []
                }
            
            methodology_counts = Counter(methodologies)
            
            # Define common research methodologies
            common_methodologies = {
                "experimental", "survey", "case study", "systematic review",
                "meta-analysis", "qualitative", "quantitative", "mixed methods",
                "longitudinal", "cross-sectional", "ethnographic", "comparative",
                "observational", "correlational", "descriptive", "exploratory"
            }
            
            covered_methodologies = set(methodology_counts.keys())
            missing_methodologies = common_methodologies - covered_methodologies
            
            # Identify underused methodologies
            underused = [
                {
                    "methodology": method,
                    "count": count,
                    "percentage": round(count / len(items) * 100, 2),
                    "last_used": max(methodology_years[method]) if methodology_years[method] else None,
                    "topics_used_with": list(methodology_topics[method])
                }
                for method, count in methodology_counts.items()
                if count <= 2
            ]
            
            # Analyze methodology-topic combinations
            methodology_topic_gaps = await self._analyze_methodology_topic_gaps(
                methodology_topics, methodology_counts
            )
            
            return {
                "gaps": {
                    "missing_methodologies": list(missing_methodologies)[:10],
                    "underused_methodologies": underused,
                    "methodology_topic_gaps": methodology_topic_gaps
                },
                "analysis": {
                    "total_methodologies_used": len(covered_methodologies),
                    "methodology_diversity_score": len(covered_methodologies) / len(common_methodologies),
                    "most_common_methodologies": methodology_counts.most_common(5),
                    "methodology_distribution": dict(methodology_counts)
                },
                "recommendations": [
                    f"Consider using {method} methodology" for method in list(missing_methodologies)[:5]
                ] + [
                    f"Increase use of {gap['methodology']} (currently {gap['count']} papers)"
                    for gap in underused[:3]
                ]
            }
            
        except Exception as e:
            logger.warning(f"Error detecting methodological gaps: {e}")
            return {"error": "Failed to detect methodological gaps", "gaps": []}
    
    async def _generate_gap_filling_recommendations(self, gaps: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations to fill identified gaps"""
        try:
            recommendations = []
            
            # Process temporal gaps
            if "temporal" in gaps and gaps["temporal"].get("gaps"):
                for gap in gaps["temporal"]["gaps"]:
                    if gap["type"] == "publication_gap":
                        recommendations.append({
                            "type": "temporal",
                            "priority": "high" if gap["severity"] == "high" else "medium",
                            "title": f"Fill publication gap ({gap['start_year']}-{gap['end_year']})",
                            "description": f"Add research from {gap['gap_size']} missing years",
                            "specific_years": gap["missing_years"],
                            "action": "search_and_add_papers"
                        })
                    elif gap["type"] == "recent_gap":
                        recommendations.append({
                            "type": "temporal",
                            "priority": "high",
                            "title": "Update with recent publications",
                            "description": f"Add papers from {gap['last_publication']} to {gap['current_year']}",
                            "years_behind": gap["gap_size"],
                            "action": "add_recent_papers"
                        })
            
            # Process topical gaps
            if "topical" in gaps and gaps["topical"].get("gaps"):
                topical_gaps = gaps["topical"]["gaps"]
                
                # Underrepresented topics
                if "underrepresented_topics" in topical_gaps:
                    for topic_gap in topical_gaps["underrepresented_topics"][:5]:
                        recommendations.append({
                            "type": "topical",
                            "priority": topic_gap["severity"],
                            "title": f"Expand research on {topic_gap['topic']}",
                            "description": f"Currently only {topic_gap['count']} papers ({topic_gap['percentage']}%)",
                            "topic": topic_gap["topic"],
                            "current_coverage": topic_gap["count"],
                            "action": "add_topic_papers"
                        })
                
                # Missing topics
                if gaps["topical"].get("suggestions", {}).get("missing_topics"):
                    for missing_topic in gaps["topical"]["suggestions"]["missing_topics"][:3]:
                        recommendations.append({
                            "type": "topical",
                            "priority": "medium",
                            "title": f"Consider research on {missing_topic}",
                            "description": f"This topic appears to be missing from your collection",
                            "topic": missing_topic,
                            "action": "explore_new_topic"
                        })
            
            # Process methodological gaps
            if "methodological" in gaps and gaps["methodological"].get("gaps"):
                method_gaps = gaps["methodological"]["gaps"]
                
                # Missing methodologies
                if "missing_methodologies" in method_gaps:
                    for method in method_gaps["missing_methodologies"][:3]:
                        recommendations.append({
                            "type": "methodological",
                            "priority": "medium",
                            "title": f"Explore {method} methodology",
                            "description": f"This methodology is not represented in your collection",
                            "methodology": method,
                            "action": "add_methodology_papers"
                        })
                
                # Underused methodologies
                if "underused_methodologies" in method_gaps:
                    for method_gap in method_gaps["underused_methodologies"][:3]:
                        recommendations.append({
                            "type": "methodological",
                            "priority": "low",
                            "title": f"Increase use of {method_gap['methodology']}",
                            "description": f"Currently only {method_gap['count']} papers use this methodology",
                            "methodology": method_gap["methodology"],
                            "current_usage": method_gap["count"],
                            "action": "expand_methodology_usage"
                        })
            
            # Sort recommendations by priority
            priority_order = {"high": 3, "medium": 2, "low": 1}
            recommendations.sort(key=lambda x: priority_order.get(x["priority"], 0), reverse=True)
            
            return recommendations[:15]  # Return top 15 recommendations
            
        except Exception as e:
            logger.warning(f"Error generating gap-filling recommendations: {e}")
            return []
    
    async def _analyze_temporal_trends(self, items: List[ZoteroItem]) -> Dict[str, Any]:
        """Analyze temporal trends in research"""
        try:
            # Group items by year
            items_by_year = defaultdict(list)
            for item in items:
                if item.publication_year:
                    items_by_year[item.publication_year].append(item)
            
            if not items_by_year:
                return {"error": "No items with publication years for temporal trend analysis"}
            
            years = sorted(items_by_year.keys())
            
            # Calculate publication trends
            publication_counts = [len(items_by_year[year]) for year in years]
            
            # Calculate growth rate
            growth_rates = []
            for i in range(1, len(publication_counts)):
                if publication_counts[i-1] > 0:
                    growth_rate = (publication_counts[i] - publication_counts[i-1]) / publication_counts[i-1] * 100
                    growth_rates.append(growth_rate)
            
            avg_growth_rate = sum(growth_rates) / len(growth_rates) if growth_rates else 0
            
            # Identify peak and low years
            max_year = years[publication_counts.index(max(publication_counts))]
            min_year = years[publication_counts.index(min(publication_counts))]
            
            # Calculate trend direction using linear regression
            if len(years) > 2:
                x = np.array(range(len(years)))
                y = np.array(publication_counts)
                slope = np.polyfit(x, y, 1)[0]
                trend_direction = "increasing" if slope > 0.1 else "decreasing" if slope < -0.1 else "stable"
            else:
                trend_direction = "insufficient_data"
            
            return {
                "publication_timeline": {
                    "years": years,
                    "counts": publication_counts,
                    "total_publications": sum(publication_counts)
                },
                "trend_analysis": {
                    "direction": trend_direction,
                    "average_growth_rate": round(avg_growth_rate, 2),
                    "peak_year": {"year": max_year, "count": max(publication_counts)},
                    "lowest_year": {"year": min_year, "count": min(publication_counts)},
                    "volatility": round(np.std(publication_counts), 2) if len(publication_counts) > 1 else 0
                },
                "patterns": {
                    "consistent_years": len([c for c in publication_counts if c >= np.mean(publication_counts)]),
                    "productive_periods": self._identify_productive_periods(years, publication_counts),
                    "research_phases": self._identify_research_phases(years, publication_counts)
                }
            }
            
        except Exception as e:
            logger.warning(f"Error analyzing temporal trends: {e}")
            return {"error": "Failed to analyze temporal trends"}
    
    async def _analyze_topical_trends(self, items: List[ZoteroItem]) -> Dict[str, Any]:
        """Analyze topical trends in research"""
        try:
            # Extract topics by year
            topics_by_year = defaultdict(list)
            all_topics = set()
            
            for item in items:
                if item.publication_year and self._has_topic_analysis(item):
                    analysis = item.item_metadata["ai_analysis"]["results"]["topics"]
                    primary_topics = analysis.get("primary_topics", [])
                    
                    for topic in primary_topics:
                        topics_by_year[item.publication_year].append(topic.lower())
                        all_topics.add(topic.lower())
            
            if not topics_by_year:
                return {"error": "No topic data available for trend analysis"}
            
            years = sorted(topics_by_year.keys())
            
            # Track topic evolution
            topic_evolution = {}
            for topic in all_topics:
                topic_years = []
                topic_counts = []
                
                for year in years:
                    count = topics_by_year[year].count(topic)
                    if count > 0:
                        topic_years.append(year)
                        topic_counts.append(count)
                
                if len(topic_years) > 1:
                    # Calculate trend for this topic
                    if len(topic_counts) > 2:
                        slope = np.polyfit(range(len(topic_counts)), topic_counts, 1)[0]
                        trend = "increasing" if slope > 0.1 else "decreasing" if slope < -0.1 else "stable"
                    else:
                        trend = "stable"
                    
                    topic_evolution[topic] = {
                        "first_appearance": min(topic_years),
                        "latest_appearance": max(topic_years),
                        "total_papers": sum(topic_counts),
                        "trend": trend,
                        "peak_year": topic_years[topic_counts.index(max(topic_counts))],
                        "peak_count": max(topic_counts)
                    }
            
            # Identify emerging and declining topics
            emerging_topics = [
                topic for topic, data in topic_evolution.items()
                if data["trend"] == "increasing" and data["latest_appearance"] >= max(years) - 2
            ]
            
            declining_topics = [
                topic for topic, data in topic_evolution.items()
                if data["trend"] == "decreasing" and data["latest_appearance"] < max(years) - 1
            ]
            
            # Calculate topic diversity over time
            diversity_by_year = {}
            for year in years:
                unique_topics = len(set(topics_by_year[year]))
                total_topics = len(topics_by_year[year])
                diversity_by_year[year] = {
                    "unique_topics": unique_topics,
                    "total_mentions": total_topics,
                    "diversity_ratio": unique_topics / total_topics if total_topics > 0 else 0
                }
            
            return {
                "topic_evolution": topic_evolution,
                "trending_topics": {
                    "emerging": emerging_topics[:5],
                    "declining": declining_topics[:5],
                    "stable": [
                        topic for topic, data in topic_evolution.items()
                        if data["trend"] == "stable"
                    ][:5]
                },
                "diversity_analysis": {
                    "by_year": diversity_by_year,
                    "overall_trend": self._calculate_diversity_trend(diversity_by_year),
                    "most_diverse_year": max(diversity_by_year.keys(), key=lambda y: diversity_by_year[y]["diversity_ratio"]) if diversity_by_year else None
                },
                "topic_lifecycle": {
                    "new_topics_per_year": {
                        year: len([t for t, d in topic_evolution.items() if d["first_appearance"] == year])
                        for year in years
                    },
                    "topic_persistence": {
                        "short_term": len([t for t, d in topic_evolution.items() if d["latest_appearance"] - d["first_appearance"] <= 1]),
                        "medium_term": len([t for t, d in topic_evolution.items() if 1 < d["latest_appearance"] - d["first_appearance"] <= 3]),
                        "long_term": len([t for t, d in topic_evolution.items() if d["latest_appearance"] - d["first_appearance"] > 3])
                    }
                }
            }
            
        except Exception as e:
            logger.warning(f"Error analyzing topical trends: {e}")
            return {"error": "Failed to analyze topical trends"}
    
    async def _analyze_citation_trends(self, items: List[ZoteroItem]) -> Dict[str, Any]:
        """Analyze citation trends"""
        try:
            # Analyze publication venues over time
            venues_by_year = defaultdict(list)
            all_venues = set()
            
            for item in items:
                if item.publication_year and item.publication_title:
                    venue = item.publication_title.strip()
                    venues_by_year[item.publication_year].append(venue)
                    all_venues.add(venue)
            
            if not venues_by_year:
                return {"error": "No publication venue data available for citation trend analysis"}
            
            years = sorted(venues_by_year.keys())
            
            # Track venue popularity over time
            venue_trends = {}
            for venue in all_venues:
                venue_years = []
                venue_counts = []
                
                for year in years:
                    count = venues_by_year[year].count(venue)
                    if count > 0:
                        venue_years.append(year)
                        venue_counts.append(count)
                
                if len(venue_years) > 0:
                    venue_trends[venue] = {
                        "first_publication": min(venue_years),
                        "latest_publication": max(venue_years),
                        "total_papers": sum(venue_counts),
                        "active_years": len(venue_years),
                        "average_papers_per_year": sum(venue_counts) / len(venue_years)
                    }
            
            # Identify top venues by different metrics
            top_venues_by_count = sorted(venue_trends.items(), key=lambda x: x[1]["total_papers"], reverse=True)[:10]
            top_venues_by_consistency = sorted(
                venue_trends.items(), 
                key=lambda x: x[1]["active_years"], 
                reverse=True
            )[:10]
            
            # Analyze venue diversity
            venue_diversity_by_year = {}
            for year in years:
                unique_venues = len(set(venues_by_year[year]))
                total_publications = len(venues_by_year[year])
                venue_diversity_by_year[year] = {
                    "unique_venues": unique_venues,
                    "total_publications": total_publications,
                    "diversity_ratio": unique_venues / total_publications if total_publications > 0 else 0
                }
            
            # Calculate citation impact patterns (simplified)
            impact_analysis = await self._analyze_publication_impact(items)
            
            return {
                "venue_analysis": {
                    "total_unique_venues": len(all_venues),
                    "top_venues_by_count": [(venue, data["total_papers"]) for venue, data in top_venues_by_count],
                    "top_venues_by_consistency": [(venue, data["active_years"]) for venue, data in top_venues_by_consistency],
                    "venue_trends": venue_trends
                },
                "diversity_trends": {
                    "by_year": venue_diversity_by_year,
                    "overall_trend": self._calculate_diversity_trend(venue_diversity_by_year),
                    "most_diverse_year": max(venue_diversity_by_year.keys(), key=lambda y: venue_diversity_by_year[y]["diversity_ratio"]) if venue_diversity_by_year else None
                },
                "publication_patterns": {
                    "venue_loyalty": len([v for v, d in venue_trends.items() if d["total_papers"] >= 3]),
                    "venue_exploration": len([v for v, d in venue_trends.items() if d["total_papers"] == 1]),
                    "average_venues_per_year": sum(len(set(venues)) for venues in venues_by_year.values()) / len(years) if years else 0
                },
                "impact_analysis": impact_analysis
            }
            
        except Exception as e:
            logger.warning(f"Error analyzing citation trends: {e}")
            return {"error": "Failed to analyze citation trends"}
    
    async def _analyze_collaboration_trends(self, items: List[ZoteroItem]) -> Dict[str, Any]:
        """Analyze collaboration trends"""
        try:
            # Extract author collaboration data by year
            collaborations_by_year = defaultdict(list)
            all_authors = set()
            author_years = defaultdict(list)
            
            for item in items:
                if item.publication_year and item.creators:
                    authors = []
                    for creator in item.creators:
                        if isinstance(creator, dict) and creator.get("creatorType") == "author":
                            name = f"{creator.get('firstName', '')} {creator.get('lastName', '')}".strip()
                            if name:
                                authors.append(name)
                                all_authors.add(name)
                                author_years[name].append(item.publication_year)
                    
                    if len(authors) > 1:
                        # Record collaboration
                        collaborations_by_year[item.publication_year].append({
                            "authors": authors,
                            "collaboration_size": len(authors),
                            "item_id": item.id
                        })
            
            if not collaborations_by_year:
                return {"error": "No collaboration data available for trend analysis"}
            
            years = sorted(collaborations_by_year.keys())
            
            # Analyze collaboration patterns over time
            collaboration_metrics_by_year = {}
            for year in years:
                collabs = collaborations_by_year[year]
                if collabs:
                    sizes = [c["collaboration_size"] for c in collabs]
                    collaboration_metrics_by_year[year] = {
                        "total_collaborations": len(collabs),
                        "average_collaboration_size": round(sum(sizes) / len(sizes), 2),
                        "max_collaboration_size": max(sizes),
                        "min_collaboration_size": min(sizes),
                        "unique_authors": len(set(author for collab in collabs for author in collab["authors"]))
                    }
            
            # Identify prolific authors and their collaboration patterns
            author_productivity = {}
            for author in all_authors:
                years_active = sorted(set(author_years[author]))
                total_papers = len(author_years[author])
                
                # Count collaborations for this author
                collaborations = 0
                for year_collabs in collaborations_by_year.values():
                    for collab in year_collabs:
                        if author in collab["authors"]:
                            collaborations += 1
                
                author_productivity[author] = {
                    "total_papers": total_papers,
                    "years_active": len(years_active),
                    "first_year": min(years_active) if years_active else None,
                    "latest_year": max(years_active) if years_active else None,
                    "collaborations": collaborations,
                    "collaboration_rate": collaborations / total_papers if total_papers > 0 else 0
                }
            
            # Identify collaboration trends
            top_collaborators = sorted(
                author_productivity.items(), 
                key=lambda x: x[1]["collaboration_rate"], 
                reverse=True
            )[:10]
            
            most_productive = sorted(
                author_productivity.items(), 
                key=lambda x: x[1]["total_papers"], 
                reverse=True
            )[:10]
            
            # Calculate network metrics
            network_evolution = await self._analyze_collaboration_network_evolution(collaborations_by_year)
            
            return {
                "collaboration_metrics": {
                    "by_year": collaboration_metrics_by_year,
                    "overall_trends": {
                        "total_unique_authors": len(all_authors),
                        "average_collaboration_size": round(
                            sum(metrics["average_collaboration_size"] for metrics in collaboration_metrics_by_year.values()) / len(collaboration_metrics_by_year), 2
                        ) if collaboration_metrics_by_year else 0,
                        "collaboration_growth": self._calculate_collaboration_growth(collaboration_metrics_by_year)
                    }
                },
                "author_analysis": {
                    "top_collaborators": [(author, data["collaboration_rate"]) for author, data in top_collaborators],
                    "most_productive": [(author, data["total_papers"]) for author, data in most_productive],
                    "author_longevity": {
                        "long_term_authors": len([a for a, d in author_productivity.items() if d["years_active"] >= 5]),
                        "consistent_authors": len([a for a, d in author_productivity.items() if d["years_active"] >= 3]),
                        "new_authors": len([a for a, d in author_productivity.items() if d["years_active"] == 1])
                    }
                },
                "network_evolution": network_evolution,
                "collaboration_patterns": {
                    "solo_work_trend": self._calculate_solo_work_trend(items, years),
                    "team_size_evolution": self._analyze_team_size_evolution(collaboration_metrics_by_year),
                    "author_retention": self._calculate_author_retention(author_years, years)
                }
            }
            
        except Exception as e:
            logger.warning(f"Error analyzing collaboration trends: {e}")
            return {"error": "Failed to analyze collaboration trends"}
    
    async def _generate_trend_predictions(self, trends: Dict[str, Any]) -> Dict[str, Any]:
        """Generate predictions based on identified trends"""
        try:
            predictions = {
                "temporal_predictions": [],
                "topical_predictions": [],
                "collaboration_predictions": [],
                "venue_predictions": [],
                "confidence_scores": {}
            }
            
            # Temporal predictions
            if "temporal" in trends and "trend_analysis" in trends["temporal"]:
                temporal_data = trends["temporal"]["trend_analysis"]
                
                if temporal_data["direction"] == "increasing":
                    predictions["temporal_predictions"].append({
                        "prediction": "Research activity likely to continue increasing",
                        "basis": f"Average growth rate of {temporal_data['average_growth_rate']}%",
                        "confidence": "medium" if abs(temporal_data["average_growth_rate"]) > 5 else "low"
                    })
                elif temporal_data["direction"] == "decreasing":
                    predictions["temporal_predictions"].append({
                        "prediction": "Research activity may decline without intervention",
                        "basis": f"Negative growth rate of {temporal_data['average_growth_rate']}%",
                        "confidence": "medium"
                    })
                
                # Predict next year's activity
                if "publication_timeline" in trends["temporal"]:
                    recent_counts = trends["temporal"]["publication_timeline"]["counts"][-3:]
                    if len(recent_counts) >= 2:
                        avg_recent = sum(recent_counts) / len(recent_counts)
                        predictions["temporal_predictions"].append({
                            "prediction": f"Expected {int(avg_recent)} publications next year",
                            "basis": f"Based on recent average of {avg_recent:.1f} papers",
                            "confidence": "low"
                        })
            
            # Topical predictions
            if "topical" in trends and "trending_topics" in trends["topical"]:
                topical_data = trends["topical"]["trending_topics"]
                
                if topical_data.get("emerging"):
                    predictions["topical_predictions"].append({
                        "prediction": f"Emerging topics likely to grow: {', '.join(topical_data['emerging'][:3])}",
                        "basis": "Topics showing increasing trend in recent years",
                        "confidence": "medium"
                    })
                
                if topical_data.get("declining"):
                    predictions["topical_predictions"].append({
                        "prediction": f"Topics may need attention: {', '.join(topical_data['declining'][:3])}",
                        "basis": "Topics showing declining trend",
                        "confidence": "medium"
                    })
            
            # Collaboration predictions
            if "collaboration" in trends and "collaboration_metrics" in trends["collaboration"]:
                collab_data = trends["collaboration"]["collaboration_metrics"]
                
                if "overall_trends" in collab_data:
                    growth = collab_data["overall_trends"].get("collaboration_growth", 0)
                    if growth > 0:
                        predictions["collaboration_predictions"].append({
                            "prediction": "Collaboration levels likely to increase",
                            "basis": f"Collaboration growth rate of {growth:.1f}%",
                            "confidence": "medium"
                        })
                    elif growth < -5:
                        predictions["collaboration_predictions"].append({
                            "prediction": "May need to foster more collaboration",
                            "basis": f"Declining collaboration rate of {growth:.1f}%",
                            "confidence": "medium"
                        })
            
            # Generate AI-powered predictions
            ai_predictions = await self._generate_ai_predictions(trends)
            if ai_predictions:
                predictions["ai_insights"] = ai_predictions
            
            # Calculate overall confidence scores
            predictions["confidence_scores"] = {
                "temporal": self._calculate_prediction_confidence(trends.get("temporal", {})),
                "topical": self._calculate_prediction_confidence(trends.get("topical", {})),
                "collaboration": self._calculate_prediction_confidence(trends.get("collaboration", {})),
                "overall": "medium"  # Conservative overall confidence
            }
            
            return predictions
            
        except Exception as e:
            logger.warning(f"Error generating trend predictions: {e}")
            return {"error": "Failed to generate trend predictions"}
    
    async def _generate_theme_insights(self, theme: Dict[str, Any]) -> List[str]:
        """Generate insights for a research theme"""
        try:
            insights = []
            
            # Basic theme insights
            if theme.get("item_count", 0) > 0:
                insights.append(f"This theme encompasses {theme['item_count']} research papers")
            
            if theme.get("coherence_score", 0) > 0.7:
                insights.append("High coherence suggests well-defined research area")
            elif theme.get("coherence_score", 0) < 0.3:
                insights.append("Low coherence may indicate diverse or emerging research area")
            
            # Keyword-based insights
            keywords = theme.get("keywords", [])
            if keywords:
                if len(keywords) > 5:
                    insights.append(f"Broad theme with {len(keywords)} key concepts")
                else:
                    insights.append(f"Focused theme centered on {', '.join(keywords[:3])}")
            
            # Generate AI-powered insights
            ai_insights = await self._generate_ai_theme_insights(theme)
            if ai_insights:
                insights.extend(ai_insights)
            
            # Add methodological insights if available
            items = theme.get("items", [])
            if items:
                # Analyze publication years in theme
                years = [item.get("year") for item in items if item.get("year")]
                if years:
                    year_span = max(years) - min(years) if len(years) > 1 else 0
                    if year_span > 5:
                        insights.append(f"Long-term research theme spanning {year_span} years")
                    elif year_span < 2:
                        insights.append("Recent or focused research theme")
            
            return insights[:5]  # Return top 5 insights
            
        except Exception as e:
            logger.warning(f"Error generating theme insights: {e}")
            return ["Theme analysis completed"]
    
    async def _suggest_research_directions(self, theme: Dict[str, Any]) -> List[str]:
        """Suggest future research directions for a theme"""
        try:
            directions = []
            
            keywords = theme.get("keywords", [])
            theme_name = theme.get("theme_name", "research theme")
            
            # Generate direction suggestions based on keywords
            if keywords:
                # Suggest interdisciplinary connections
                directions.append(f"Explore interdisciplinary applications of {keywords[0]} in related fields")
                
                # Suggest methodological extensions
                if len(keywords) > 1:
                    directions.append(f"Investigate the relationship between {keywords[0]} and {keywords[1]}")
                
                # Suggest practical applications
                directions.append(f"Develop practical applications of {theme_name} research")
            
            # Analyze theme items for specific suggestions
            items = theme.get("items", [])
            if items:
                # Suggest based on publication timeline
                years = [item.get("year") for item in items if item.get("year")]
                if years:
                    latest_year = max(years)
                    current_year = datetime.now().year
                    if current_year - latest_year > 2:
                        directions.append(f"Update {theme_name} research with recent developments")
            
            # Generate AI-powered research directions
            ai_directions = await self._generate_ai_research_directions(theme)
            if ai_directions:
                directions.extend(ai_directions)
            
            # Add gap-based suggestions
            if theme.get("coherence_score", 0) < 0.5:
                directions.append(f"Strengthen theoretical foundations of {theme_name}")
            
            if theme.get("item_count", 0) < 5:
                directions.append(f"Expand literature coverage in {theme_name}")
            
            return directions[:5]  # Return top 5 directions
            
        except Exception as e:
            logger.warning(f"Error suggesting research directions: {e}")
            return ["Continue current research trajectory", "Explore related methodologies"]
    
    # Helper methods for advanced analysis
    async def _analyze_topic_relationships(self, topics: List[str], topic_item_map: Dict[str, List[str]]) -> Dict[str, Any]:
        """Analyze relationships between topics"""
        try:
            topic_counts = Counter(topics)
            
            # Find isolated topics (topics that rarely co-occur with others)
            isolated_topics = []
            for topic, items in topic_item_map.items():
                if len(items) <= 2:  # Topics with very few papers
                    isolated_topics.append({
                        "topic": topic,
                        "paper_count": len(items),
                        "isolation_score": 1.0 - (len(items) / len(topic_item_map))
                    })
            
            # Find potential missing connections
            missing_connections = []
            common_topics = [topic for topic, count in topic_counts.most_common(10)]
            
            for i, topic1 in enumerate(common_topics):
                for topic2 in common_topics[i+1:]:
                    # Check if these topics ever appear together
                    items1 = set(topic_item_map[topic1])
                    items2 = set(topic_item_map[topic2])
                    overlap = len(items1.intersection(items2))
                    
                    if overlap == 0 and len(items1) > 2 and len(items2) > 2:
                        missing_connections.append({
                            "topic1": topic1,
                            "topic2": topic2,
                            "potential_connection": f"Explore connections between {topic1} and {topic2}"
                        })
            
            return {
                "isolated_topics": isolated_topics[:5],
                "missing_connections": missing_connections[:5]
            }
            
        except Exception as e:
            logger.warning(f"Error analyzing topic relationships: {e}")
            return {"isolated_topics": [], "missing_connections": []}
    
    async def _suggest_missing_topics(self, existing_topics: List[str]) -> List[str]:
        """Suggest topics that might be missing from the collection"""
        try:
            # Define topic clusters and suggest related topics
            topic_clusters = {
                "machine learning": ["deep learning", "neural networks", "reinforcement learning", "supervised learning"],
                "artificial intelligence": ["machine learning", "natural language processing", "computer vision", "robotics"],
                "data science": ["machine learning", "statistics", "data mining", "big data"],
                "healthcare": ["medical informatics", "telemedicine", "health analytics", "clinical decision support"],
                "finance": ["fintech", "algorithmic trading", "risk management", "blockchain"],
                "education": ["e-learning", "educational technology", "learning analytics", "MOOCs"],
                "security": ["cybersecurity", "privacy", "cryptography", "network security"],
                "software engineering": ["software architecture", "testing", "agile development", "DevOps"]
            }
            
            existing_lower = [topic.lower() for topic in existing_topics]
            suggestions = []
            
            for main_topic, related_topics in topic_clusters.items():
                if main_topic in existing_lower:
                    for related in related_topics:
                        if related not in existing_lower:
                            suggestions.append(related)
            
            # Add general suggestions based on common research areas
            general_suggestions = [
                "systematic review", "meta-analysis", "case study", "survey research",
                "experimental design", "qualitative research", "mixed methods"
            ]
            
            for suggestion in general_suggestions:
                if suggestion not in existing_lower:
                    suggestions.append(suggestion)
            
            return list(set(suggestions))[:10]  # Return unique suggestions
            
        except Exception as e:
            logger.warning(f"Error suggesting missing topics: {e}")
            return []
    
    async def _analyze_methodology_topic_gaps(self, methodology_topics: Dict[str, set], methodology_counts: Counter) -> List[Dict[str, Any]]:
        """Analyze gaps in methodology-topic combinations"""
        try:
            gaps = []
            
            # Find methodologies that are only used with limited topics
            for methodology, topics in methodology_topics.items():
                if len(topics) <= 2 and methodology_counts[methodology] >= 2:
                    gaps.append({
                        "methodology": methodology,
                        "current_topics": list(topics),
                        "topic_count": len(topics),
                        "paper_count": methodology_counts[methodology],
                        "suggestion": f"Apply {methodology} to more diverse topics"
                    })
            
            # Find topics that could benefit from more methodological diversity
            topic_methodologies = defaultdict(set)
            for methodology, topics in methodology_topics.items():
                for topic in topics:
                    topic_methodologies[topic].add(methodology)
            
            for topic, methodologies in topic_methodologies.items():
                if len(methodologies) == 1:
                    gaps.append({
                        "type": "topic_methodology_gap",
                        "topic": topic,
                        "current_methodologies": list(methodologies),
                        "methodology_count": len(methodologies),
                        "suggestion": f"Explore different methodologies for {topic} research"
                    })
            
            return gaps[:10]
            
        except Exception as e:
            logger.warning(f"Error analyzing methodology-topic gaps: {e}")
            return []
    
    def _identify_productive_periods(self, years: List[int], counts: List[int]) -> List[Dict[str, Any]]:
        """Identify periods of high research productivity"""
        try:
            if len(years) < 3:
                return []
            
            avg_count = sum(counts) / len(counts)
            productive_periods = []
            
            current_period = None
            for i, (year, count) in enumerate(zip(years, counts)):
                if count >= avg_count * 1.2:  # 20% above average
                    if current_period is None:
                        current_period = {"start": year, "end": year, "papers": count}
                    else:
                        current_period["end"] = year
                        current_period["papers"] += count
                else:
                    if current_period is not None:
                        if current_period["end"] > current_period["start"]:  # Multi-year period
                            productive_periods.append(current_period)
                        current_period = None
            
            # Don't forget the last period
            if current_period is not None and current_period["end"] > current_period["start"]:
                productive_periods.append(current_period)
            
            return productive_periods
            
        except Exception as e:
            logger.warning(f"Error identifying productive periods: {e}")
            return []
    
    def _identify_research_phases(self, years: List[int], counts: List[int]) -> List[Dict[str, Any]]:
        """Identify distinct phases in research activity"""
        try:
            if len(years) < 5:
                return []
            
            phases = []
            
            # Simple phase detection based on activity level changes
            avg_count = sum(counts) / len(counts)
            
            current_phase = None
            for i, (year, count) in enumerate(zip(years, counts)):
                phase_type = "high" if count >= avg_count else "low"
                
                if current_phase is None or current_phase["type"] != phase_type:
                    if current_phase is not None:
                        phases.append(current_phase)
                    current_phase = {
                        "type": phase_type,
                        "start": year,
                        "end": year,
                        "duration": 1,
                        "total_papers": count
                    }
                else:
                    current_phase["end"] = year
                    current_phase["duration"] += 1
                    current_phase["total_papers"] += count
            
            if current_phase is not None:
                phases.append(current_phase)
            
            return phases
            
        except Exception as e:
            logger.warning(f"Error identifying research phases: {e}")
            return []
    
    def _calculate_diversity_trend(self, diversity_by_year: Dict[int, Dict[str, Any]]) -> str:
        """Calculate overall diversity trend"""
        try:
            if len(diversity_by_year) < 2:
                return "insufficient_data"
            
            years = sorted(diversity_by_year.keys())
            diversity_ratios = [diversity_by_year[year]["diversity_ratio"] for year in years]
            
            # Simple trend calculation
            if len(diversity_ratios) > 2:
                slope = np.polyfit(range(len(diversity_ratios)), diversity_ratios, 1)[0]
                if slope > 0.01:
                    return "increasing"
                elif slope < -0.01:
                    return "decreasing"
                else:
                    return "stable"
            else:
                return "stable"
                
        except Exception as e:
            logger.warning(f"Error calculating diversity trend: {e}")
            return "unknown"
    
    async def _analyze_publication_impact(self, items: List[ZoteroItem]) -> Dict[str, Any]:
        """Analyze publication impact patterns (simplified)"""
        try:
            # Analyze by publication type
            type_counts = Counter([item.item_type for item in items if item.item_type])
            
            # Analyze by DOI availability (proxy for impact)
            items_with_doi = len([item for item in items if item.doi])
            doi_percentage = (items_with_doi / len(items)) * 100 if items else 0
            
            # Analyze publication recency
            current_year = datetime.now().year
            recent_items = len([item for item in items if item.publication_year and item.publication_year >= current_year - 3])
            recency_percentage = (recent_items / len(items)) * 100 if items else 0
            
            return {
                "publication_types": dict(type_counts),
                "doi_coverage": {
                    "items_with_doi": items_with_doi,
                    "percentage": round(doi_percentage, 2)
                },
                "recency_analysis": {
                    "recent_items": recent_items,
                    "percentage": round(recency_percentage, 2)
                },
                "impact_indicators": {
                    "journal_articles": type_counts.get("journalArticle", 0),
                    "conference_papers": type_counts.get("conferencePaper", 0),
                    "books": type_counts.get("book", 0)
                }
            }
            
        except Exception as e:
            logger.warning(f"Error analyzing publication impact: {e}")
            return {}
    
    async def _analyze_collaboration_network_evolution(self, collaborations_by_year: Dict[int, List[Dict]]) -> Dict[str, Any]:
        """Analyze how collaboration networks evolve over time"""
        try:
            evolution = {}
            
            for year, collabs in collaborations_by_year.items():
                # Build network for this year
                authors_this_year = set()
                connections_this_year = 0
                
                for collab in collabs:
                    authors = collab["authors"]
                    authors_this_year.update(authors)
                    # Count connections (pairs of authors)
                    connections_this_year += len(authors) * (len(authors) - 1) // 2
                
                evolution[year] = {
                    "unique_authors": len(authors_this_year),
                    "total_connections": connections_this_year,
                    "network_density": connections_this_year / (len(authors_this_year) * (len(authors_this_year) - 1) // 2) if len(authors_this_year) > 1 else 0
                }
            
            return {
                "yearly_evolution": evolution,
                "network_growth": {
                    "author_growth": self._calculate_network_growth([data["unique_authors"] for data in evolution.values()]),
                    "connection_growth": self._calculate_network_growth([data["total_connections"] for data in evolution.values()])
                }
            }
            
        except Exception as e:
            logger.warning(f"Error analyzing collaboration network evolution: {e}")
            return {}
    
    def _calculate_collaboration_growth(self, metrics_by_year: Dict[int, Dict[str, Any]]) -> float:
        """Calculate collaboration growth rate"""
        try:
            if len(metrics_by_year) < 2:
                return 0.0
            
            years = sorted(metrics_by_year.keys())
            collab_counts = [metrics_by_year[year]["total_collaborations"] for year in years]
            
            if len(collab_counts) > 1 and collab_counts[0] > 0:
                growth_rate = (collab_counts[-1] - collab_counts[0]) / collab_counts[0] * 100
                return round(growth_rate, 2)
            
            return 0.0
            
        except Exception as e:
            logger.warning(f"Error calculating collaboration growth: {e}")
            return 0.0
    
    def _calculate_solo_work_trend(self, items: List[ZoteroItem], years: List[int]) -> Dict[str, Any]:
        """Calculate trend in solo vs collaborative work"""
        try:
            solo_by_year = {}
            
            for year in years:
                year_items = [item for item in items if item.publication_year == year]
                solo_count = 0
                total_count = 0
                
                for item in year_items:
                    if item.creators:
                        authors = [c for c in item.creators if isinstance(c, dict) and c.get("creatorType") == "author"]
                        total_count += 1
                        if len(authors) == 1:
                            solo_count += 1
                
                if total_count > 0:
                    solo_by_year[year] = {
                        "solo_papers": solo_count,
                        "total_papers": total_count,
                        "solo_percentage": (solo_count / total_count) * 100
                    }
            
            return {
                "by_year": solo_by_year,
                "overall_trend": self._calculate_trend_direction([data["solo_percentage"] for data in solo_by_year.values()])
            }
            
        except Exception as e:
            logger.warning(f"Error calculating solo work trend: {e}")
            return {}
    
    def _analyze_team_size_evolution(self, metrics_by_year: Dict[int, Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze how team sizes evolve over time"""
        try:
            team_sizes = []
            years = sorted(metrics_by_year.keys())
            
            for year in years:
                avg_size = metrics_by_year[year].get("average_collaboration_size", 0)
                team_sizes.append(avg_size)
            
            return {
                "average_sizes_by_year": dict(zip(years, team_sizes)),
                "trend": self._calculate_trend_direction(team_sizes),
                "size_range": {
                    "min": min(team_sizes) if team_sizes else 0,
                    "max": max(team_sizes) if team_sizes else 0,
                    "average": sum(team_sizes) / len(team_sizes) if team_sizes else 0
                }
            }
            
        except Exception as e:
            logger.warning(f"Error analyzing team size evolution: {e}")
            return {}
    
    def _calculate_author_retention(self, author_years: Dict[str, List[int]], years: List[int]) -> Dict[str, Any]:
        """Calculate author retention rates"""
        try:
            if len(years) < 2:
                return {"error": "Insufficient years for retention analysis"}
            
            retention_data = {}
            
            for i in range(len(years) - 1):
                current_year = years[i]
                next_year = years[i + 1]
                
                current_authors = set([author for author, author_year_list in author_years.items() if current_year in author_year_list])
                next_authors = set([author for author, author_year_list in author_years.items() if next_year in author_year_list])
                
                retained = len(current_authors.intersection(next_authors))
                retention_rate = (retained / len(current_authors)) * 100 if current_authors else 0
                
                retention_data[f"{current_year}-{next_year}"] = {
                    "retained_authors": retained,
                    "total_authors": len(current_authors),
                    "retention_rate": round(retention_rate, 2)
                }
            
            avg_retention = sum([data["retention_rate"] for data in retention_data.values()]) / len(retention_data) if retention_data else 0
            
            return {
                "by_year_transition": retention_data,
                "average_retention_rate": round(avg_retention, 2)
            }
            
        except Exception as e:
            logger.warning(f"Error calculating author retention: {e}")
            return {}
    
    def _calculate_network_growth(self, values: List[int]) -> str:
        """Calculate network growth trend"""
        try:
            if len(values) < 2:
                return "insufficient_data"
            
            return self._calculate_trend_direction(values)
            
        except Exception as e:
            logger.warning(f"Error calculating network growth: {e}")
            return "unknown"
    
    async def _generate_ai_predictions(self, trends: Dict[str, Any]) -> List[str]:
        """Generate AI-powered predictions based on trends"""
        try:
            # Prepare trend summary for AI analysis
            trend_summary = self._prepare_trend_summary(trends)
            
            prompt = f"""
            Based on the following research trends analysis, provide 3-5 specific predictions about future research directions:
            
            {trend_summary}
            
            Focus on:
            1. Emerging research opportunities
            2. Potential collaboration patterns
            3. Topic evolution predictions
            4. Methodological developments
            
            Provide concise, actionable predictions.
            """
            
            response = await self._call_llm(prompt)
            
            if response:
                # Parse AI response into individual predictions
                predictions = [pred.strip() for pred in response.split('\n') if pred.strip() and not pred.strip().startswith('#')]
                return predictions[:5]
            
            return []
            
        except Exception as e:
            logger.warning(f"Error generating AI predictions: {e}")
            return []
    
    def _prepare_trend_summary(self, trends: Dict[str, Any]) -> str:
        """Prepare a summary of trends for AI analysis"""
        try:
            summary_parts = []
            
            if "temporal" in trends:
                temporal = trends["temporal"]
                if "trend_analysis" in temporal:
                    direction = temporal["trend_analysis"].get("direction", "unknown")
                    growth = temporal["trend_analysis"].get("average_growth_rate", 0)
                    summary_parts.append(f"Publication trend: {direction} (growth rate: {growth}%)")
            
            if "topical" in trends:
                topical = trends["topical"]
                if "trending_topics" in topical:
                    emerging = topical["trending_topics"].get("emerging", [])
                    declining = topical["trending_topics"].get("declining", [])
                    if emerging:
                        summary_parts.append(f"Emerging topics: {', '.join(emerging[:3])}")
                    if declining:
                        summary_parts.append(f"Declining topics: {', '.join(declining[:3])}")
            
            if "collaboration" in trends:
                collab = trends["collaboration"]
                if "collaboration_metrics" in collab:
                    growth = collab["collaboration_metrics"]["overall_trends"].get("collaboration_growth", 0)
                    summary_parts.append(f"Collaboration growth: {growth}%")
            
            return "; ".join(summary_parts) if summary_parts else "Limited trend data available"
            
        except Exception as e:
            logger.warning(f"Error preparing trend summary: {e}")
            return "Trend analysis data unavailable"
    
    def _calculate_prediction_confidence(self, trend_data: Dict[str, Any]) -> str:
        """Calculate confidence level for predictions"""
        try:
            confidence_factors = 0
            total_factors = 0
            
            # Check data completeness
            if trend_data:
                total_factors += 1
                if len(trend_data) > 2:  # Multiple data points
                    confidence_factors += 1
            
            # Check trend consistency
            if "trend_analysis" in trend_data:
                total_factors += 1
                direction = trend_data["trend_analysis"].get("direction")
                if direction in ["increasing", "decreasing"]:
                    confidence_factors += 1
            
            # Calculate confidence
            if total_factors == 0:
                return "low"
            
            confidence_ratio = confidence_factors / total_factors
            if confidence_ratio >= 0.7:
                return "high"
            elif confidence_ratio >= 0.4:
                return "medium"
            else:
                return "low"
                
        except Exception as e:
            logger.warning(f"Error calculating prediction confidence: {e}")
            return "low"
    
    async def _generate_ai_theme_insights(self, theme: Dict[str, Any]) -> List[str]:
        """Generate AI-powered insights for a research theme"""
        try:
            keywords = theme.get("keywords", [])[:5]
            item_count = theme.get("item_count", 0)
            coherence = theme.get("coherence_score", 0)
            
            prompt = f"""
            Analyze this research theme and provide 2-3 specific insights:
            
            Theme keywords: {', '.join(keywords)}
            Number of papers: {item_count}
            Coherence score: {coherence:.2f}
            
            Provide insights about:
            1. The research maturity and development stage
            2. Potential research gaps or opportunities
            3. Interdisciplinary connections
            
            Keep insights concise and actionable.
            """
            
            response = await self._call_llm(prompt)
            
            if response:
                insights = [insight.strip() for insight in response.split('\n') if insight.strip() and not insight.strip().startswith('#')]
                return insights[:3]
            
            return []
            
        except Exception as e:
            logger.warning(f"Error generating AI theme insights: {e}")
            return []
    
    async def _generate_ai_research_directions(self, theme: Dict[str, Any]) -> List[str]:
        """Generate AI-powered research directions for a theme"""
        try:
            keywords = theme.get("keywords", [])[:5]
            theme_name = theme.get("theme_name", "research theme")
            
            prompt = f"""
            Suggest 2-3 future research directions for this theme:
            
            Theme: {theme_name}
            Key concepts: {', '.join(keywords)}
            
            Focus on:
            1. Emerging methodologies or technologies
            2. Unexplored applications or domains
            3. Interdisciplinary opportunities
            
            Provide specific, actionable research directions.
            """
            
            response = await self._call_llm(prompt)
            
            if response:
                directions = [direction.strip() for direction in response.split('\n') if direction.strip() and not direction.strip().startswith('#')]
                return directions[:3]
            
            return []
            
        except Exception as e:
            logger.warning(f"Error generating AI research directions: {e}")
            return []