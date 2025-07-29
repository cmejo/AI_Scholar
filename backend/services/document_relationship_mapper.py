"""
Document Relationship Mapper for connection visualization and analysis
"""
import asyncio
import json
import logging
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Set
from collections import defaultdict, Counter
from dataclasses import dataclass
from datetime import datetime
import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from core.database import (
    get_db, Document, DocumentChunk, DocumentChunkEnhanced, 
    KnowledgeGraphEntity, KnowledgeGraphRelationship, DocumentTag,
    AnalyticsEvent, User
)
from models.schemas import DocumentResponse

logger = logging.getLogger(__name__)

@dataclass
class DocumentSimilarity:
    """Document similarity information"""
    document1_id: str
    document1_name: str
    document2_id: str
    document2_name: str
    similarity_score: float
    similarity_type: str  # content, semantic, entity, tag
    shared_entities: List[str]
    shared_tags: List[str]
    common_topics: List[str]

@dataclass
class DocumentConnection:
    """Document connection information"""
    source_document_id: str
    target_document_id: str
    connection_type: str  # similarity, citation, entity_overlap, topic_overlap
    strength: float
    metadata: Dict[str, Any]

@dataclass
class DocumentCluster:
    """Document cluster information"""
    cluster_id: int
    documents: List[str]
    centroid_topics: List[str]
    cluster_name: str
    coherence_score: float

@dataclass
class DocumentRelationshipMap:
    """Complete document relationship mapping"""
    documents: List[DocumentResponse]
    similarities: List[DocumentSimilarity]
    connections: List[DocumentConnection]
    clusters: List[DocumentCluster]
    network_metrics: Dict[str, Any]
    visualization_data: Dict[str, Any]

class DocumentRelationshipMapper:
    """Service for mapping and analyzing document relationships"""
    
    def __init__(self, db: Session):
        self.db = db
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.8
        )
        
    async def analyze_document_relationships(
        self,
        user_id: str,
        similarity_threshold: float = 0.3,
        include_clusters: bool = True
    ) -> DocumentRelationshipMap:
        """Analyze relationships between all user documents"""
        try:
            # Get user documents
            documents = self.db.query(Document).filter(
                Document.user_id == user_id
            ).all()
            
            if len(documents) < 2:
                return DocumentRelationshipMap(
                    documents=[DocumentResponse.model_validate(doc) for doc in documents],
                    similarities=[],
                    connections=[],
                    clusters=[],
                    network_metrics={},
                    visualization_data={}
                )
            
            logger.info(f"Analyzing relationships for {len(documents)} documents")
            
            # Calculate similarities
            similarities = await self._calculate_document_similarities(
                documents, similarity_threshold
            )
            
            # Generate connections
            connections = await self._generate_document_connections(
                documents, similarities
            )
            
            # Perform clustering if requested
            clusters = []
            if include_clusters and len(documents) >= 3:
                clusters = await self._cluster_documents(documents)
            
            # Calculate network metrics
            network_metrics = await self._calculate_network_metrics(
                documents, connections
            )
            
            # Generate visualization data
            visualization_data = await self._generate_visualization_data(
                documents, connections, clusters
            )
            
            return DocumentRelationshipMap(
                documents=[DocumentResponse.model_validate(doc) for doc in documents],
                similarities=similarities,
                connections=connections,
                clusters=clusters,
                network_metrics=network_metrics,
                visualization_data=visualization_data
            )
            
        except Exception as e:
            logger.error(f"Error analyzing document relationships: {str(e)}")
            raise

    async def _calculate_document_similarities(
        self,
        documents: List[Document],
        threshold: float
    ) -> List[DocumentSimilarity]:
        """Calculate similarities between documents using multiple methods"""
        similarities = []
        
        try:
            # Content-based similarity using TF-IDF
            content_similarities = await self._calculate_content_similarity(documents)
            similarities.extend(content_similarities)
            
            # Entity-based similarity
            entity_similarities = await self._calculate_entity_similarity(documents)
            similarities.extend(entity_similarities)
            
            # Tag-based similarity
            tag_similarities = await self._calculate_tag_similarity(documents)
            similarities.extend(tag_similarities)
            
            # Filter by threshold
            similarities = [s for s in similarities if s.similarity_score >= threshold]
            
            # Sort by similarity score
            similarities.sort(key=lambda x: x.similarity_score, reverse=True)
            
            return similarities
            
        except Exception as e:
            logger.error(f"Error calculating document similarities: {str(e)}")
            return []

    async def _calculate_content_similarity(
        self,
        documents: List[Document]
    ) -> List[DocumentSimilarity]:
        """Calculate content similarity using TF-IDF and cosine similarity"""
        similarities = []
        
        try:
            # Get document contents
            doc_contents = []
            doc_info = []
            
            for doc in documents:
                # Get document chunks for content
                chunks = self.db.query(DocumentChunk).filter(
                    DocumentChunk.document_id == doc.id
                ).all()
                
                content = " ".join([chunk.content for chunk in chunks])
                if content.strip():
                    doc_contents.append(content)
                    doc_info.append(doc)
            
            if len(doc_contents) < 2:
                return similarities
            
            # Calculate TF-IDF vectors
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(doc_contents)
            
            # Calculate cosine similarity
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            # Extract similarities above threshold
            for i in range(len(doc_info)):
                for j in range(i + 1, len(doc_info)):
                    score = similarity_matrix[i][j]
                    
                    if score > 0.1:  # Minimum threshold for content similarity
                        similarities.append(DocumentSimilarity(
                            document1_id=doc_info[i].id,
                            document1_name=doc_info[i].name,
                            document2_id=doc_info[j].id,
                            document2_name=doc_info[j].name,
                            similarity_score=float(score),
                            similarity_type="content",
                            shared_entities=[],
                            shared_tags=[],
                            common_topics=await self._extract_common_topics(
                                doc_info[i], doc_info[j]
                            )
                        ))
            
            return similarities
            
        except Exception as e:
            logger.error(f"Error calculating content similarity: {str(e)}")
            return []

    async def _calculate_entity_similarity(
        self,
        documents: List[Document]
    ) -> List[DocumentSimilarity]:
        """Calculate similarity based on shared entities"""
        similarities = []
        
        try:
            # Get entities for each document
            doc_entities = {}
            for doc in documents:
                entities = self.db.query(KnowledgeGraphEntity).filter(
                    KnowledgeGraphEntity.document_id == doc.id
                ).all()
                doc_entities[doc.id] = {e.name.lower() for e in entities}
            
            # Calculate entity overlap
            for i, doc1 in enumerate(documents):
                for j, doc2 in enumerate(documents[i + 1:], i + 1):
                    entities1 = doc_entities.get(doc1.id, set())
                    entities2 = doc_entities.get(doc2.id, set())
                    
                    if not entities1 or not entities2:
                        continue
                    
                    # Calculate Jaccard similarity
                    intersection = entities1.intersection(entities2)
                    union = entities1.union(entities2)
                    
                    if union:
                        jaccard_score = len(intersection) / len(union)
                        
                        if jaccard_score > 0.1:
                            similarities.append(DocumentSimilarity(
                                document1_id=doc1.id,
                                document1_name=doc1.name,
                                document2_id=doc2.id,
                                document2_name=doc2.name,
                                similarity_score=jaccard_score,
                                similarity_type="entity",
                                shared_entities=list(intersection),
                                shared_tags=[],
                                common_topics=[]
                            ))
            
            return similarities
            
        except Exception as e:
            logger.error(f"Error calculating entity similarity: {str(e)}")
            return []

    async def _calculate_tag_similarity(
        self,
        documents: List[Document]
    ) -> List[DocumentSimilarity]:
        """Calculate similarity based on shared tags"""
        similarities = []
        
        try:
            # Get tags for each document
            doc_tags = {}
            for doc in documents:
                tags = self.db.query(DocumentTag).filter(
                    DocumentTag.document_id == doc.id
                ).all()
                doc_tags[doc.id] = {t.tag_name.lower() for t in tags}
            
            # Calculate tag overlap
            for i, doc1 in enumerate(documents):
                for j, doc2 in enumerate(documents[i + 1:], i + 1):
                    tags1 = doc_tags.get(doc1.id, set())
                    tags2 = doc_tags.get(doc2.id, set())
                    
                    if not tags1 or not tags2:
                        continue
                    
                    # Calculate Jaccard similarity
                    intersection = tags1.intersection(tags2)
                    union = tags1.union(tags2)
                    
                    if union:
                        jaccard_score = len(intersection) / len(union)
                        
                        if jaccard_score > 0.1:
                            similarities.append(DocumentSimilarity(
                                document1_id=doc1.id,
                                document1_name=doc1.name,
                                document2_id=doc2.id,
                                document2_name=doc2.name,
                                similarity_score=jaccard_score,
                                similarity_type="tag",
                                shared_entities=[],
                                shared_tags=list(intersection),
                                common_topics=[]
                            ))
            
            return similarities
            
        except Exception as e:
            logger.error(f"Error calculating tag similarity: {str(e)}")
            return []

    async def _extract_common_topics(
        self,
        doc1: Document,
        doc2: Document
    ) -> List[str]:
        """Extract common topics between two documents"""
        try:
            # Get tags for both documents
            tags1 = self.db.query(DocumentTag).filter(
                DocumentTag.document_id == doc1.id,
                DocumentTag.tag_type == 'topic'
            ).all()
            
            tags2 = self.db.query(DocumentTag).filter(
                DocumentTag.document_id == doc2.id,
                DocumentTag.tag_type == 'topic'
            ).all()
            
            topics1 = {tag.tag_name.lower() for tag in tags1}
            topics2 = {tag.tag_name.lower() for tag in tags2}
            
            return list(topics1.intersection(topics2))
            
        except Exception as e:
            logger.error(f"Error extracting common topics: {str(e)}")
            return []

    async def _generate_document_connections(
        self,
        documents: List[Document],
        similarities: List[DocumentSimilarity]
    ) -> List[DocumentConnection]:
        """Generate document connections from similarities"""
        connections = []
        
        try:
            for similarity in similarities:
                # Determine connection strength based on similarity type and score
                strength = similarity.similarity_score
                
                # Boost strength for entity-based connections
                if similarity.similarity_type == "entity" and similarity.shared_entities:
                    strength *= 1.2
                
                # Boost strength for tag-based connections
                if similarity.similarity_type == "tag" and similarity.shared_tags:
                    strength *= 1.1
                
                connections.append(DocumentConnection(
                    source_document_id=similarity.document1_id,
                    target_document_id=similarity.document2_id,
                    connection_type=f"{similarity.similarity_type}_similarity",
                    strength=min(strength, 1.0),  # Cap at 1.0
                    metadata={
                        "similarity_score": similarity.similarity_score,
                        "shared_entities": similarity.shared_entities,
                        "shared_tags": similarity.shared_tags,
                        "common_topics": similarity.common_topics
                    }
                ))
            
            return connections
            
        except Exception as e:
            logger.error(f"Error generating document connections: {str(e)}")
            return []

    async def _cluster_documents(
        self,
        documents: List[Document],
        n_clusters: Optional[int] = None
    ) -> List[DocumentCluster]:
        """Cluster documents based on content similarity"""
        clusters = []
        
        try:
            # Get document contents for clustering
            doc_contents = []
            doc_mapping = {}
            
            for doc in documents:
                chunks = self.db.query(DocumentChunk).filter(
                    DocumentChunk.document_id == doc.id
                ).all()
                
                content = " ".join([chunk.content for chunk in chunks])
                if content.strip():
                    doc_contents.append(content)
                    doc_mapping[len(doc_contents) - 1] = doc
            
            if len(doc_contents) < 3:
                return clusters
            
            # Determine optimal number of clusters
            if n_clusters is None:
                n_clusters = min(5, max(2, len(doc_contents) // 3))
            
            # Create TF-IDF vectors
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(doc_contents)
            
            # Perform K-means clustering
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(tfidf_matrix)
            
            # Group documents by cluster
            cluster_groups = defaultdict(list)
            for idx, label in enumerate(cluster_labels):
                if idx in doc_mapping:
                    cluster_groups[label].append(doc_mapping[idx])
            
            # Create cluster objects
            feature_names = self.tfidf_vectorizer.get_feature_names_out()
            
            for cluster_id, docs in cluster_groups.items():
                if len(docs) >= 2:  # Only include clusters with multiple documents
                    # Get top terms for cluster centroid
                    centroid = kmeans.cluster_centers_[cluster_id]
                    top_indices = centroid.argsort()[-10:][::-1]
                    centroid_topics = [feature_names[i] for i in top_indices]
                    
                    # Generate cluster name from top topics
                    cluster_name = f"Cluster {cluster_id + 1}: {', '.join(centroid_topics[:3])}"
                    
                    # Calculate coherence score (simplified)
                    coherence_score = float(np.mean(centroid[top_indices[:5]]))
                    
                    clusters.append(DocumentCluster(
                        cluster_id=cluster_id,
                        documents=[doc.id for doc in docs],
                        centroid_topics=centroid_topics,
                        cluster_name=cluster_name,
                        coherence_score=coherence_score
                    ))
            
            return clusters
            
        except Exception as e:
            logger.error(f"Error clustering documents: {str(e)}")
            return []

    async def _calculate_network_metrics(
        self,
        documents: List[Document],
        connections: List[DocumentConnection]
    ) -> Dict[str, Any]:
        """Calculate network metrics for document relationships"""
        try:
            # Create NetworkX graph
            G = nx.Graph()
            
            # Add nodes
            for doc in documents:
                G.add_node(doc.id, name=doc.name, size=doc.size)
            
            # Add edges
            for conn in connections:
                G.add_edge(
                    conn.source_document_id,
                    conn.target_document_id,
                    weight=conn.strength,
                    type=conn.connection_type
                )
            
            # Calculate metrics
            metrics = {
                "total_documents": len(documents),
                "total_connections": len(connections),
                "network_density": nx.density(G) if G.number_of_nodes() > 1 else 0,
                "average_clustering": nx.average_clustering(G) if G.number_of_nodes() > 2 else 0,
                "connected_components": nx.number_connected_components(G),
                "largest_component_size": len(max(nx.connected_components(G), key=len)) if G.number_of_nodes() > 0 else 0
            }
            
            # Calculate centrality measures
            if G.number_of_nodes() > 1:
                degree_centrality = nx.degree_centrality(G)
                betweenness_centrality = nx.betweenness_centrality(G)
                closeness_centrality = nx.closeness_centrality(G)
                
                # Find most central documents
                most_central_degree = max(degree_centrality.items(), key=lambda x: x[1])
                most_central_betweenness = max(betweenness_centrality.items(), key=lambda x: x[1])
                
                metrics.update({
                    "most_connected_document": {
                        "id": most_central_degree[0],
                        "degree_centrality": most_central_degree[1]
                    },
                    "most_bridging_document": {
                        "id": most_central_betweenness[0],
                        "betweenness_centrality": most_central_betweenness[1]
                    },
                    "average_degree_centrality": sum(degree_centrality.values()) / len(degree_centrality),
                    "average_betweenness_centrality": sum(betweenness_centrality.values()) / len(betweenness_centrality)
                })
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating network metrics: {str(e)}")
            return {}

    async def _generate_visualization_data(
        self,
        documents: List[Document],
        connections: List[DocumentConnection],
        clusters: List[DocumentCluster]
    ) -> Dict[str, Any]:
        """Generate data for network visualization"""
        try:
            # Create nodes for visualization
            nodes = []
            cluster_map = {}
            
            # Map documents to clusters
            for cluster in clusters:
                for doc_id in cluster.documents:
                    cluster_map[doc_id] = {
                        "cluster_id": cluster.cluster_id,
                        "cluster_name": cluster.cluster_name
                    }
            
            for doc in documents:
                # Calculate node size based on connections
                connection_count = sum(
                    1 for conn in connections
                    if conn.source_document_id == doc.id or conn.target_document_id == doc.id
                )
                
                node_size = max(10, min(50, 10 + connection_count * 5))
                
                cluster_info = cluster_map.get(doc.id, {"cluster_id": -1, "cluster_name": "Unclustered"})
                
                nodes.append({
                    "id": doc.id,
                    "name": doc.name,
                    "size": node_size,
                    "cluster": cluster_info["cluster_id"],
                    "cluster_name": cluster_info["cluster_name"],
                    "document_size": doc.size,
                    "created_at": doc.created_at.isoformat() if doc.created_at else None
                })
            
            # Create edges for visualization
            edges = []
            for conn in connections:
                edges.append({
                    "source": conn.source_document_id,
                    "target": conn.target_document_id,
                    "weight": conn.strength,
                    "type": conn.connection_type,
                    "metadata": conn.metadata
                })
            
            # Create cluster visualization data
            cluster_viz = []
            for cluster in clusters:
                cluster_viz.append({
                    "id": cluster.cluster_id,
                    "name": cluster.cluster_name,
                    "documents": cluster.documents,
                    "topics": cluster.centroid_topics[:5],
                    "coherence": cluster.coherence_score,
                    "size": len(cluster.documents)
                })
            
            return {
                "nodes": nodes,
                "edges": edges,
                "clusters": cluster_viz,
                "layout_suggestions": {
                    "force_directed": True,
                    "cluster_layout": len(clusters) > 0,
                    "hierarchical": False
                },
                "color_scheme": {
                    "content_similarity": "#3498db",
                    "entity_similarity": "#e74c3c",
                    "tag_similarity": "#2ecc71",
                    "default": "#95a5a6"
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating visualization data: {str(e)}")
            return {}

    async def get_document_connections(
        self,
        document_id: str,
        user_id: str,
        max_connections: int = 10
    ) -> List[DocumentConnection]:
        """Get connections for a specific document"""
        try:
            # Verify document ownership
            document = self.db.query(Document).filter(
                Document.id == document_id,
                Document.user_id == user_id
            ).first()
            
            if not document:
                return []
            
            # Get all user documents for relationship analysis
            all_docs = self.db.query(Document).filter(
                Document.user_id == user_id
            ).all()
            
            if len(all_docs) < 2:
                return []
            
            # Calculate similarities for this document
            similarities = await self._calculate_document_similarities(all_docs, 0.1)
            
            # Filter connections for this document
            relevant_similarities = [
                s for s in similarities
                if s.document1_id == document_id or s.document2_id == document_id
            ]
            
            # Generate connections
            connections = await self._generate_document_connections(all_docs, relevant_similarities)
            
            # Filter and sort connections
            document_connections = [
                conn for conn in connections
                if conn.source_document_id == document_id or conn.target_document_id == document_id
            ]
            
            # Sort by strength and limit
            document_connections.sort(key=lambda x: x.strength, reverse=True)
            return document_connections[:max_connections]
            
        except Exception as e:
            logger.error(f"Error getting document connections: {str(e)}")
            return []

    async def get_relationship_insights(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """Get insights about document relationships"""
        try:
            relationship_map = await self.analyze_document_relationships(user_id)
            
            insights = {
                "total_documents": len(relationship_map.documents),
                "total_connections": len(relationship_map.connections),
                "similarity_distribution": {},
                "cluster_analysis": {},
                "network_insights": relationship_map.network_metrics,
                "recommendations": []
            }
            
            # Analyze similarity distribution
            similarity_types = Counter(s.similarity_type for s in relationship_map.similarities)
            insights["similarity_distribution"] = dict(similarity_types)
            
            # Analyze clusters
            if relationship_map.clusters:
                insights["cluster_analysis"] = {
                    "total_clusters": len(relationship_map.clusters),
                    "largest_cluster_size": max(len(c.documents) for c in relationship_map.clusters),
                    "average_cluster_size": sum(len(c.documents) for c in relationship_map.clusters) / len(relationship_map.clusters),
                    "cluster_topics": [c.centroid_topics[:3] for c in relationship_map.clusters]
                }
            
            # Generate recommendations
            recommendations = []
            
            if insights["total_connections"] == 0:
                recommendations.append("No document connections found. Consider uploading related documents to build a knowledge network.")
            elif insights["total_connections"] < insights["total_documents"] * 0.5:
                recommendations.append("Low document connectivity. Consider adding more related content or improving document tagging.")
            
            if relationship_map.network_metrics.get("network_density", 0) < 0.3:
                recommendations.append("Document network has low density. Adding bridging documents could improve knowledge discovery.")
            
            if len(relationship_map.clusters) > 0:
                isolated_docs = insights["total_documents"] - sum(len(c.documents) for c in relationship_map.clusters)
                if isolated_docs > 0:
                    recommendations.append(f"{isolated_docs} documents are not clustered. Consider adding connecting content or improving categorization.")
            
            insights["recommendations"] = recommendations
            
            return insights
            
        except Exception as e:
            logger.error(f"Error getting relationship insights: {str(e)}")
            return {}