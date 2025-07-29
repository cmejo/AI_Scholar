"""
Topic Modeling Service for content analysis and document clustering
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, Counter
from dataclasses import dataclass
import numpy as np

from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.cluster import KMeans, DBSCAN
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc

from core.database import (
    get_db, Document, DocumentChunk, DocumentTag, AnalyticsEvent,
    User, UserProfile
)
from models.schemas import DocumentTagCreate, AnalyticsEventCreate

logger = logging.getLogger(__name__)

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')

@dataclass
class TopicInfo:
    """Information about a discovered topic"""
    id: int
    name: str
    keywords: List[str]
    coherence_score: float
    document_count: int
    weight: float
    description: str

@dataclass
class DocumentCluster:
    """Information about a document cluster"""
    id: int
    name: str
    documents: List[str]  # document IDs
    centroid_keywords: List[str]
    similarity_threshold: float
    cluster_size: int
    representative_doc_id: str

@dataclass
class TopicTrend:
    """Topic trend information over time"""
    topic_id: int
    topic_name: str
    time_series: Dict[str, float]  # date -> topic strength
    trend_direction: str  # 'increasing', 'decreasing', 'stable'
    growth_rate: float
    peak_date: str
    current_strength: float

@dataclass
class TopicModelingResult:
    """Complete topic modeling analysis result"""
    topics: List[TopicInfo]
    document_clusters: List[DocumentCluster]
    topic_trends: List[TopicTrend]
    document_topic_assignments: Dict[str, List[Tuple[int, float]]]  # doc_id -> [(topic_id, weight)]
    model_metadata: Dict[str, Any]

class TopicModelingService:
    """Service for topic modeling and document clustering"""
    
    def __init__(self, db: Session):
        self.db = db
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        
        # Model parameters
        self.n_topics = 10
        self.n_clusters = 8
        self.min_df = 2
        self.max_df = 0.8
        self.random_state = 42
        
    async def analyze_document_topics(
        self,
        user_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None,
        n_topics: Optional[int] = None,
        update_tags: bool = True
    ) -> TopicModelingResult:
        """
        Perform comprehensive topic modeling analysis on documents
        """
        try:
            logger.info(f"Starting topic modeling analysis for user {user_id}")
            
            # Set number of topics
            if n_topics:
                self.n_topics = n_topics
            
            # Get documents to analyze
            documents = await self._get_documents_for_analysis(user_id, document_ids)
            
            if len(documents) < 2:
                logger.warning("Not enough documents for topic modeling")
                return TopicModelingResult(
                    topics=[],
                    document_clusters=[],
                    topic_trends=[],
                    document_topic_assignments={},
                    model_metadata={"error": "Insufficient documents for analysis"}
                )
            
            # Prepare document texts
            doc_texts, doc_metadata = await self._prepare_document_texts(documents)
            
            # Perform topic modeling
            topics, doc_topic_assignments = await self._perform_topic_modeling(doc_texts, doc_metadata)
            
            # Perform document clustering
            clusters = await self._perform_document_clustering(doc_texts, doc_metadata)
            
            # Analyze topic trends
            trends = await self._analyze_topic_trends(topics, doc_metadata, user_id)
            
            # Update document tags if requested
            if update_tags:
                await self._update_document_tags(doc_topic_assignments, topics)
            
            # Track analytics event
            await self._track_topic_modeling_event(user_id, len(documents), len(topics))
            
            result = TopicModelingResult(
                topics=topics,
                document_clusters=clusters,
                topic_trends=trends,
                document_topic_assignments=doc_topic_assignments,
                model_metadata={
                    "n_documents": len(documents),
                    "n_topics": len(topics),
                    "n_clusters": len(clusters),
                    "analysis_timestamp": datetime.utcnow().isoformat(),
                    "parameters": {
                        "n_topics": self.n_topics,
                        "n_clusters": self.n_clusters,
                        "min_df": self.min_df,
                        "max_df": self.max_df
                    }
                }
            )
            
            logger.info(f"Topic modeling analysis completed: {len(topics)} topics, {len(clusters)} clusters")
            return result
            
        except Exception as e:
            logger.error(f"Error in topic modeling analysis: {str(e)}")
            raise

    async def _get_documents_for_analysis(
        self,
        user_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None
    ) -> List[Document]:
        """Get documents for topic modeling analysis"""
        try:
            query = self.db.query(Document).filter(Document.status == "completed")
            
            if user_id:
                query = query.filter(Document.user_id == user_id)
            
            if document_ids:
                query = query.filter(Document.id.in_(document_ids))
            
            documents = query.all()
            logger.info(f"Retrieved {len(documents)} documents for analysis")
            return documents
            
        except Exception as e:
            logger.error(f"Error retrieving documents: {str(e)}")
            raise

    async def _prepare_document_texts(
        self,
        documents: List[Document]
    ) -> Tuple[List[str], List[Dict[str, Any]]]:
        """Prepare document texts and metadata for analysis"""
        try:
            doc_texts = []
            doc_metadata = []
            
            for doc in documents:
                # Get document chunks
                chunks = self.db.query(DocumentChunk).filter(
                    DocumentChunk.document_id == doc.id
                ).all()
                
                # Combine chunk content
                full_text = " ".join([chunk.content for chunk in chunks])
                
                # Preprocess text
                processed_text = await self._preprocess_text(full_text)
                
                if processed_text.strip():  # Only include non-empty texts
                    doc_texts.append(processed_text)
                    doc_metadata.append({
                        "document_id": doc.id,
                        "document_name": doc.name,
                        "content_type": doc.content_type,
                        "size": doc.size,
                        "created_at": doc.created_at,
                        "user_id": doc.user_id
                    })
            
            logger.info(f"Prepared {len(doc_texts)} document texts for analysis")
            return doc_texts, doc_metadata
            
        except Exception as e:
            logger.error(f"Error preparing document texts: {str(e)}")
            raise

    async def _preprocess_text(self, text: str) -> str:
        """Preprocess text for topic modeling"""
        try:
            # Convert to lowercase
            text = text.lower()
            
            # Tokenize
            tokens = word_tokenize(text)
            
            # Remove stopwords and non-alphabetic tokens
            tokens = [
                token for token in tokens 
                if token.isalpha() and token not in self.stop_words and len(token) > 2
            ]
            
            # Lemmatize
            tokens = [self.lemmatizer.lemmatize(token) for token in tokens]
            
            return " ".join(tokens)
            
        except Exception as e:
            logger.error(f"Error preprocessing text: {str(e)}")
            return text

    async def _perform_topic_modeling(
        self,
        doc_texts: List[str],
        doc_metadata: List[Dict[str, Any]]
    ) -> Tuple[List[TopicInfo], Dict[str, List[Tuple[int, float]]]]:
        """Perform LDA topic modeling"""
        try:
            # Create TF-IDF vectorizer
            vectorizer = TfidfVectorizer(
                max_features=1000,
                min_df=self.min_df,
                max_df=self.max_df,
                ngram_range=(1, 2)
            )
            
            # Fit and transform documents
            doc_term_matrix = vectorizer.fit_transform(doc_texts)
            feature_names = vectorizer.get_feature_names_out()
            
            # Perform LDA
            lda_model = LatentDirichletAllocation(
                n_components=self.n_topics,
                random_state=self.random_state,
                max_iter=100,
                learning_method='batch'
            )
            
            lda_model.fit(doc_term_matrix)
            doc_topic_probs = lda_model.transform(doc_term_matrix)
            
            # Extract topics
            topics = []
            for topic_idx, topic in enumerate(lda_model.components_):
                # Get top keywords for this topic
                top_keywords_idx = topic.argsort()[-10:][::-1]
                keywords = [feature_names[i] for i in top_keywords_idx]
                
                # Calculate topic statistics
                topic_weights = doc_topic_probs[:, topic_idx]
                avg_weight = np.mean(topic_weights)
                doc_count = np.sum(topic_weights > 0.1)  # Documents with >10% probability
                
                # Generate topic name and description
                topic_name = await self._generate_topic_name(keywords)
                topic_description = await self._generate_topic_description(keywords)
                
                topics.append(TopicInfo(
                    id=topic_idx,
                    name=topic_name,
                    keywords=keywords,
                    coherence_score=avg_weight,  # Simplified coherence measure
                    document_count=int(doc_count),
                    weight=float(avg_weight),
                    description=topic_description
                ))
            
            # Create document-topic assignments
            doc_topic_assignments = {}
            for doc_idx, metadata in enumerate(doc_metadata):
                doc_id = metadata["document_id"]
                topic_probs = doc_topic_probs[doc_idx]
                
                # Get topics with probability > 0.1
                significant_topics = [
                    (topic_idx, float(prob))
                    for topic_idx, prob in enumerate(topic_probs)
                    if prob > 0.1
                ]
                
                # Sort by probability
                significant_topics.sort(key=lambda x: x[1], reverse=True)
                doc_topic_assignments[doc_id] = significant_topics
            
            logger.info(f"Topic modeling completed: {len(topics)} topics identified")
            return topics, doc_topic_assignments
            
        except Exception as e:
            logger.error(f"Error in topic modeling: {str(e)}")
            raise

    async def _perform_document_clustering(
        self,
        doc_texts: List[str],
        doc_metadata: List[Dict[str, Any]]
    ) -> List[DocumentCluster]:
        """Perform document clustering based on content similarity"""
        try:
            # Create TF-IDF vectors for clustering
            vectorizer = TfidfVectorizer(
                max_features=500,
                min_df=self.min_df,
                max_df=self.max_df,
                stop_words='english'
            )
            
            tfidf_matrix = vectorizer.fit_transform(doc_texts)
            feature_names = vectorizer.get_feature_names_out()
            
            # Perform K-means clustering
            kmeans = KMeans(
                n_clusters=min(self.n_clusters, len(doc_texts)),
                random_state=self.random_state,
                n_init=10
            )
            
            cluster_labels = kmeans.fit_predict(tfidf_matrix)
            
            # Create clusters
            clusters = []
            for cluster_id in range(kmeans.n_clusters):
                # Get documents in this cluster
                cluster_doc_indices = [i for i, label in enumerate(cluster_labels) if label == cluster_id]
                cluster_doc_ids = [doc_metadata[i]["document_id"] for i in cluster_doc_indices]
                
                if not cluster_doc_ids:
                    continue
                
                # Get cluster centroid keywords
                centroid = kmeans.cluster_centers_[cluster_id]
                top_features_idx = centroid.argsort()[-10:][::-1]
                centroid_keywords = [feature_names[i] for i in top_features_idx]
                
                # Find representative document (closest to centroid)
                cluster_vectors = tfidf_matrix[cluster_doc_indices]
                distances = cosine_similarity(cluster_vectors, centroid.reshape(1, -1)).flatten()
                representative_idx = cluster_doc_indices[np.argmax(distances)]
                representative_doc_id = doc_metadata[representative_idx]["document_id"]
                
                # Generate cluster name
                cluster_name = await self._generate_cluster_name(centroid_keywords)
                
                # Calculate similarity threshold (average intra-cluster similarity)
                if len(cluster_doc_indices) > 1:
                    similarities = cosine_similarity(cluster_vectors)
                    avg_similarity = np.mean(similarities[np.triu_indices_from(similarities, k=1)])
                else:
                    avg_similarity = 1.0
                
                clusters.append(DocumentCluster(
                    id=cluster_id,
                    name=cluster_name,
                    documents=cluster_doc_ids,
                    centroid_keywords=centroid_keywords,
                    similarity_threshold=float(avg_similarity),
                    cluster_size=len(cluster_doc_ids),
                    representative_doc_id=representative_doc_id
                ))
            
            logger.info(f"Document clustering completed: {len(clusters)} clusters created")
            return clusters
            
        except Exception as e:
            logger.error(f"Error in document clustering: {str(e)}")
            raise

    async def _analyze_topic_trends(
        self,
        topics: List[TopicInfo],
        doc_metadata: List[Dict[str, Any]],
        user_id: Optional[str] = None
    ) -> List[TopicTrend]:
        """Analyze topic trends over time"""
        try:
            trends = []
            
            # Get historical document data
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=90)  # 3 months of data
            
            # Group documents by date
            docs_by_date = defaultdict(list)
            for metadata in doc_metadata:
                date_str = metadata["created_at"].strftime('%Y-%m-%d')
                docs_by_date[date_str].append(metadata)
            
            # For each topic, analyze its presence over time
            for topic in topics:
                time_series = {}
                
                # Calculate topic strength for each date
                for date_str, date_docs in docs_by_date.items():
                    topic_strength = 0.0
                    total_docs = len(date_docs)
                    
                    if total_docs > 0:
                        # This is a simplified trend analysis
                        # In a real implementation, you'd use the actual topic assignments
                        topic_strength = topic.weight * (total_docs / len(doc_metadata))
                    
                    time_series[date_str] = topic_strength
                
                # Calculate trend direction and growth rate
                if len(time_series) >= 2:
                    values = list(time_series.values())
                    recent_avg = np.mean(values[-7:]) if len(values) >= 7 else np.mean(values[-3:])
                    early_avg = np.mean(values[:7]) if len(values) >= 7 else np.mean(values[:3])
                    
                    if recent_avg > early_avg * 1.1:
                        trend_direction = "increasing"
                        growth_rate = (recent_avg - early_avg) / early_avg if early_avg > 0 else 0
                    elif recent_avg < early_avg * 0.9:
                        trend_direction = "decreasing"
                        growth_rate = (recent_avg - early_avg) / early_avg if early_avg > 0 else 0
                    else:
                        trend_direction = "stable"
                        growth_rate = 0.0
                    
                    # Find peak date
                    peak_date = max(time_series.keys(), key=lambda k: time_series[k])
                    current_strength = values[-1] if values else 0.0
                    
                    trends.append(TopicTrend(
                        topic_id=topic.id,
                        topic_name=topic.name,
                        time_series=time_series,
                        trend_direction=trend_direction,
                        growth_rate=float(growth_rate),
                        peak_date=peak_date,
                        current_strength=float(current_strength)
                    ))
            
            logger.info(f"Topic trend analysis completed: {len(trends)} trends analyzed")
            return trends
            
        except Exception as e:
            logger.error(f"Error in topic trend analysis: {str(e)}")
            return []

    async def _generate_topic_name(self, keywords: List[str]) -> str:
        """Generate a human-readable topic name from keywords"""
        try:
            # Simple approach: use top 2-3 keywords
            if len(keywords) >= 3:
                return f"{keywords[0].title()} & {keywords[1].title()}"
            elif len(keywords) >= 2:
                return f"{keywords[0].title()} & {keywords[1].title()}"
            elif len(keywords) >= 1:
                return keywords[0].title()
            else:
                return "Unknown Topic"
                
        except Exception as e:
            logger.error(f"Error generating topic name: {str(e)}")
            return "Topic"

    async def _generate_topic_description(self, keywords: List[str]) -> str:
        """Generate a topic description from keywords"""
        try:
            if len(keywords) >= 5:
                return f"This topic focuses on {', '.join(keywords[:3])}, and related concepts including {', '.join(keywords[3:5])}."
            elif len(keywords) >= 3:
                return f"This topic covers {', '.join(keywords[:3])} and related concepts."
            else:
                return f"This topic relates to {', '.join(keywords)}."
                
        except Exception as e:
            logger.error(f"Error generating topic description: {str(e)}")
            return "Topic description unavailable."

    async def _generate_cluster_name(self, keywords: List[str]) -> str:
        """Generate a cluster name from centroid keywords"""
        try:
            if len(keywords) >= 2:
                return f"{keywords[0].title()} Documents"
            elif len(keywords) >= 1:
                return f"{keywords[0].title()} Collection"
            else:
                return "Document Cluster"
                
        except Exception as e:
            logger.error(f"Error generating cluster name: {str(e)}")
            return "Cluster"

    async def _update_document_tags(
        self,
        doc_topic_assignments: Dict[str, List[Tuple[int, float]]],
        topics: List[TopicInfo]
    ) -> None:
        """Update document tags based on topic assignments"""
        try:
            for doc_id, topic_assignments in doc_topic_assignments.items():
                # Remove existing topic tags
                self.db.query(DocumentTag).filter(
                    DocumentTag.document_id == doc_id,
                    DocumentTag.tag_type == "topic"
                ).delete()
                
                # Add new topic tags
                for topic_id, weight in topic_assignments[:3]:  # Top 3 topics
                    if weight > 0.2:  # Only significant topics
                        topic = topics[topic_id]
                        
                        tag = DocumentTag(
                            document_id=doc_id,
                            tag_name=topic.name,
                            tag_type="topic",
                            confidence_score=weight,
                            generated_by="topic_modeling"
                        )
                        self.db.add(tag)
                
                self.db.commit()
                
            logger.info(f"Updated topic tags for {len(doc_topic_assignments)} documents")
            
        except Exception as e:
            logger.error(f"Error updating document tags: {str(e)}")
            self.db.rollback()

    async def _track_topic_modeling_event(
        self,
        user_id: Optional[str],
        n_documents: int,
        n_topics: int
    ) -> None:
        """Track topic modeling analytics event"""
        try:
            event = AnalyticsEvent(
                user_id=user_id,
                event_type="topic_modeling_performed",
                event_data={
                    "n_documents": n_documents,
                    "n_topics": n_topics,
                    "analysis_type": "full_analysis",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            self.db.add(event)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error tracking topic modeling event: {str(e)}")

    async def get_document_similarities(
        self,
        document_id: str,
        top_k: int = 10,
        similarity_threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """Get documents similar to the given document"""
        try:
            # Get the target document
            target_doc = self.db.query(Document).filter(Document.id == document_id).first()
            if not target_doc:
                raise ValueError(f"Document {document_id} not found")
            
            # Get all documents for comparison
            all_docs = self.db.query(Document).filter(
                Document.status == "completed",
                Document.id != document_id
            ).all()
            
            if not all_docs:
                return []
            
            # Prepare texts
            target_chunks = self.db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id
            ).all()
            target_text = " ".join([chunk.content for chunk in target_chunks])
            target_text = await self._preprocess_text(target_text)
            
            # Prepare comparison texts
            comparison_texts = []
            comparison_metadata = []
            
            for doc in all_docs:
                chunks = self.db.query(DocumentChunk).filter(
                    DocumentChunk.document_id == doc.id
                ).all()
                doc_text = " ".join([chunk.content for chunk in chunks])
                processed_text = await self._preprocess_text(doc_text)
                
                if processed_text.strip():
                    comparison_texts.append(processed_text)
                    comparison_metadata.append({
                        "document_id": doc.id,
                        "document_name": doc.name,
                        "content_type": doc.content_type,
                        "created_at": doc.created_at
                    })
            
            if not comparison_texts:
                return []
            
            # Calculate similarities
            all_texts = [target_text] + comparison_texts
            vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
            tfidf_matrix = vectorizer.fit_transform(all_texts)
            
            # Calculate cosine similarities
            similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
            
            # Create results
            similar_docs = []
            for i, similarity in enumerate(similarities):
                if similarity >= similarity_threshold:
                    similar_docs.append({
                        "document_id": comparison_metadata[i]["document_id"],
                        "document_name": comparison_metadata[i]["document_name"],
                        "content_type": comparison_metadata[i]["content_type"],
                        "similarity_score": float(similarity),
                        "created_at": comparison_metadata[i]["created_at"].isoformat()
                    })
            
            # Sort by similarity and return top k
            similar_docs.sort(key=lambda x: x["similarity_score"], reverse=True)
            return similar_docs[:top_k]
            
        except Exception as e:
            logger.error(f"Error calculating document similarities: {str(e)}")
            raise

    async def get_topic_insights(
        self,
        user_id: Optional[str] = None,
        time_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """Get comprehensive topic insights and analytics"""
        try:
            # Perform topic analysis
            result = await self.analyze_document_topics(user_id=user_id, update_tags=False)
            
            # Calculate additional insights
            insights = {
                "topic_summary": {
                    "total_topics": len(result.topics),
                    "total_clusters": len(result.document_clusters),
                    "most_prominent_topic": result.topics[0].name if result.topics else None,
                    "largest_cluster_size": max([c.cluster_size for c in result.document_clusters]) if result.document_clusters else 0
                },
                "topic_distribution": {
                    topic.name: {
                        "document_count": topic.document_count,
                        "weight": topic.weight,
                        "keywords": topic.keywords[:5]
                    }
                    for topic in result.topics
                },
                "cluster_analysis": {
                    f"Cluster {cluster.id}": {
                        "name": cluster.name,
                        "size": cluster.cluster_size,
                        "similarity": cluster.similarity_threshold,
                        "keywords": cluster.centroid_keywords[:5]
                    }
                    for cluster in result.document_clusters
                },
                "trending_topics": [
                    {
                        "topic_name": trend.topic_name,
                        "trend_direction": trend.trend_direction,
                        "growth_rate": trend.growth_rate,
                        "current_strength": trend.current_strength
                    }
                    for trend in result.topic_trends
                    if trend.trend_direction == "increasing"
                ][:5],
                "analysis_metadata": result.model_metadata
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Error getting topic insights: {str(e)}")
            raise