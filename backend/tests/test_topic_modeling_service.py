"""
Tests for Topic Modeling Service
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import numpy as np

from sqlalchemy.orm import Session
from services.topic_modeling_service import (
    TopicModelingService, TopicInfo, DocumentCluster, TopicTrend, TopicModelingResult
)
from core.database import Document, DocumentChunk, DocumentTag, AnalyticsEvent
from models.schemas import DocumentTagCreate

@pytest.fixture
def mock_db():
    """Mock database session"""
    return Mock(spec=Session)

@pytest.fixture
def topic_service(mock_db):
    """Create TopicModelingService instance with mocked dependencies"""
    with patch('services.topic_modeling_service.nltk'):
        service = TopicModelingService(mock_db)
        return service

@pytest.fixture
def sample_documents():
    """Sample documents for testing"""
    return [
        Document(
            id="doc1",
            user_id="user1",
            name="AI Research Paper",
            content_type="application/pdf",
            size=1024,
            status="completed",
            created_at=datetime.utcnow() - timedelta(days=10)
        ),
        Document(
            id="doc2",
            user_id="user1",
            name="Machine Learning Guide",
            content_type="application/pdf",
            size=2048,
            status="completed",
            created_at=datetime.utcnow() - timedelta(days=5)
        ),
        Document(
            id="doc3",
            user_id="user1",
            name="Data Science Handbook",
            content_type="application/pdf",
            size=3072,
            status="completed",
            created_at=datetime.utcnow() - timedelta(days=1)
        )
    ]

@pytest.fixture
def sample_chunks():
    """Sample document chunks for testing"""
    return [
        DocumentChunk(
            id="chunk1",
            document_id="doc1",
            content="Artificial intelligence and machine learning are transforming technology. Deep learning models show remarkable performance in various tasks.",
            chunk_index=0
        ),
        DocumentChunk(
            id="chunk2",
            document_id="doc1",
            content="Neural networks and deep learning architectures enable complex pattern recognition and data analysis.",
            chunk_index=1
        ),
        DocumentChunk(
            id="chunk3",
            document_id="doc2",
            content="Machine learning algorithms include supervised learning, unsupervised learning, and reinforcement learning approaches.",
            chunk_index=0
        ),
        DocumentChunk(
            id="chunk4",
            document_id="doc2",
            content="Data preprocessing and feature engineering are crucial steps in machine learning pipelines.",
            chunk_index=1
        ),
        DocumentChunk(
            id="chunk5",
            document_id="doc3",
            content="Data science combines statistics, programming, and domain expertise to extract insights from data.",
            chunk_index=0
        ),
        DocumentChunk(
            id="chunk6",
            document_id="doc3",
            content="Statistical analysis and data visualization help understand patterns and trends in datasets.",
            chunk_index=1
        )
    ]

class TestTopicModelingService:
    """Test cases for TopicModelingService"""

    @pytest.mark.asyncio
    async def test_analyze_document_topics_success(self, topic_service, mock_db, sample_documents, sample_chunks):
        """Test successful topic modeling analysis"""
        # Mock database queries
        mock_db.query.return_value.filter.return_value.all.return_value = sample_documents
        
        def mock_chunk_query(*args):
            mock_query = Mock()
            if hasattr(args[0], 'document_id'):
                # Return chunks for specific document
                doc_id = args[0].document_id
                doc_chunks = [chunk for chunk in sample_chunks if chunk.document_id == doc_id]
                mock_query.filter.return_value.all.return_value = doc_chunks
            return mock_query
        
        mock_db.query.side_effect = lambda model: mock_chunk_query(model) if model == DocumentChunk else Mock()
        mock_db.query.return_value.filter.return_value.all.return_value = sample_documents
        
        # Mock scikit-learn components
        with patch('services.topic_modeling_service.TfidfVectorizer') as mock_vectorizer, \
             patch('services.topic_modeling_service.LatentDirichletAllocation') as mock_lda, \
             patch('services.topic_modeling_service.KMeans') as mock_kmeans:
            
            # Mock vectorizer
            mock_vec_instance = Mock()
            mock_vec_instance.fit_transform.return_value = np.random.rand(3, 100)
            mock_vec_instance.get_feature_names_out.return_value = [f"word_{i}" for i in range(100)]
            mock_vectorizer.return_value = mock_vec_instance
            
            # Mock LDA
            mock_lda_instance = Mock()
            mock_lda_instance.components_ = np.random.rand(5, 100)  # 5 topics, 100 features
            mock_lda_instance.transform.return_value = np.random.rand(3, 5)  # 3 docs, 5 topics
            mock_lda.return_value = mock_lda_instance
            
            # Mock KMeans
            mock_kmeans_instance = Mock()
            mock_kmeans_instance.n_clusters = 3
            mock_kmeans_instance.fit_predict.return_value = [0, 1, 2]
            mock_kmeans_instance.cluster_centers_ = np.random.rand(3, 100)
            mock_kmeans.return_value = mock_kmeans_instance
            
            # Mock cosine similarity
            with patch('services.topic_modeling_service.cosine_similarity') as mock_cosine:
                mock_cosine.return_value = np.array([[0.8, 0.6, 0.4]])
                
                # Run analysis
                result = await topic_service.analyze_document_topics(user_id="user1")
                
                # Assertions
                assert isinstance(result, TopicModelingResult)
                assert len(result.topics) > 0
                assert len(result.document_clusters) > 0
                assert isinstance(result.model_metadata, dict)
                assert "n_documents" in result.model_metadata

    @pytest.mark.asyncio
    async def test_analyze_document_topics_insufficient_documents(self, topic_service, mock_db):
        """Test topic modeling with insufficient documents"""
        # Mock empty document list
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        result = await topic_service.analyze_document_topics(user_id="user1")
        
        assert isinstance(result, TopicModelingResult)
        assert len(result.topics) == 0
        assert len(result.document_clusters) == 0
        assert "error" in result.model_metadata

    @pytest.mark.asyncio
    async def test_get_documents_for_analysis(self, topic_service, mock_db, sample_documents):
        """Test document retrieval for analysis"""
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value.filter.return_value.all.return_value = sample_documents
        mock_db.query.return_value = mock_query
        
        documents = await topic_service._get_documents_for_analysis(user_id="user1")
        
        assert len(documents) == 3
        assert all(doc.status == "completed" for doc in sample_documents)

    @pytest.mark.asyncio
    async def test_get_documents_for_analysis_with_document_ids(self, topic_service, mock_db, sample_documents):
        """Test document retrieval with specific document IDs"""
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.all.return_value = sample_documents[:2]
        mock_db.query.return_value = mock_query
        
        documents = await topic_service._get_documents_for_analysis(
            user_id="user1",
            document_ids=["doc1", "doc2"]
        )
        
        assert len(documents) == 2

    @pytest.mark.asyncio
    async def test_prepare_document_texts(self, topic_service, mock_db, sample_documents, sample_chunks):
        """Test document text preparation"""
        def mock_chunk_query(document_id):
            return [chunk for chunk in sample_chunks if chunk.document_id == document_id]
        
        # Mock chunk queries
        mock_db.query.return_value.filter.return_value.all.side_effect = [
            mock_chunk_query("doc1"),
            mock_chunk_query("doc2"),
            mock_chunk_query("doc3")
        ]
        
        doc_texts, doc_metadata = await topic_service._prepare_document_texts(sample_documents)
        
        assert len(doc_texts) == 3
        assert len(doc_metadata) == 3
        assert all(isinstance(text, str) for text in doc_texts)
        assert all("document_id" in metadata for metadata in doc_metadata)

    @pytest.mark.asyncio
    async def test_preprocess_text(self, topic_service):
        """Test text preprocessing"""
        input_text = "This is a SAMPLE text with Stopwords and punctuation!"
        
        processed = await topic_service._preprocess_text(input_text)
        
        assert isinstance(processed, str)
        assert processed.islower()
        assert "sample" in processed
        assert "text" in processed

    @pytest.mark.asyncio
    async def test_generate_topic_name(self, topic_service):
        """Test topic name generation"""
        keywords = ["machine", "learning", "algorithm", "data", "model"]
        
        name = await topic_service._generate_topic_name(keywords)
        
        assert isinstance(name, str)
        assert len(name) > 0
        assert "Machine" in name or "Learning" in name

    @pytest.mark.asyncio
    async def test_generate_topic_description(self, topic_service):
        """Test topic description generation"""
        keywords = ["machine", "learning", "algorithm", "data", "model"]
        
        description = await topic_service._generate_topic_description(keywords)
        
        assert isinstance(description, str)
        assert len(description) > 0
        assert "topic" in description.lower()

    @pytest.mark.asyncio
    async def test_generate_cluster_name(self, topic_service):
        """Test cluster name generation"""
        keywords = ["machine", "learning", "algorithm"]
        
        name = await topic_service._generate_cluster_name(keywords)
        
        assert isinstance(name, str)
        assert len(name) > 0
        assert "Machine" in name or "Documents" in name

    @pytest.mark.asyncio
    async def test_update_document_tags(self, topic_service, mock_db):
        """Test document tag updates"""
        # Mock existing tag deletion
        mock_delete_query = Mock()
        mock_db.query.return_value.filter.return_value.filter.return_value = mock_delete_query
        
        # Sample data
        topics = [
            TopicInfo(
                id=0,
                name="Machine Learning",
                keywords=["machine", "learning"],
                coherence_score=0.8,
                document_count=2,
                weight=0.7,
                description="ML topic"
            )
        ]
        
        doc_topic_assignments = {
            "doc1": [(0, 0.8)],
            "doc2": [(0, 0.6)]
        }
        
        await topic_service._update_document_tags(doc_topic_assignments, topics)
        
        # Verify database operations
        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_get_document_similarities(self, topic_service, mock_db, sample_documents, sample_chunks):
        """Test document similarity calculation"""
        # Mock target document
        mock_db.query.return_value.filter.return_value.first.return_value = sample_documents[0]
        
        # Mock all documents query
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = sample_documents[1:]
        
        # Mock chunk queries
        def mock_chunk_side_effect(*args):
            mock_query = Mock()
            if "doc1" in str(args):
                mock_query.filter.return_value.all.return_value = [chunk for chunk in sample_chunks if chunk.document_id == "doc1"]
            elif "doc2" in str(args):
                mock_query.filter.return_value.all.return_value = [chunk for chunk in sample_chunks if chunk.document_id == "doc2"]
            elif "doc3" in str(args):
                mock_query.filter.return_value.all.return_value = [chunk for chunk in sample_chunks if chunk.document_id == "doc3"]
            return mock_query
        
        mock_db.query.side_effect = lambda model: mock_chunk_side_effect(model) if model == DocumentChunk else Mock()
        
        # Mock TF-IDF and cosine similarity
        with patch('services.topic_modeling_service.TfidfVectorizer') as mock_vectorizer, \
             patch('services.topic_modeling_service.cosine_similarity') as mock_cosine:
            
            mock_vec_instance = Mock()
            mock_vec_instance.fit_transform.return_value = np.random.rand(3, 100)
            mock_vectorizer.return_value = mock_vec_instance
            
            mock_cosine.return_value = np.array([[0.8, 0.6]])
            
            similarities = await topic_service.get_document_similarities("doc1", top_k=5)
            
            assert isinstance(similarities, list)
            assert len(similarities) <= 5
            if similarities:
                assert all("similarity_score" in sim for sim in similarities)
                assert all(sim["similarity_score"] >= 0 for sim in similarities)

    @pytest.mark.asyncio
    async def test_get_topic_insights(self, topic_service, mock_db, sample_documents, sample_chunks):
        """Test comprehensive topic insights"""
        # Mock the analyze_document_topics method
        mock_result = TopicModelingResult(
            topics=[
                TopicInfo(
                    id=0,
                    name="Machine Learning",
                    keywords=["machine", "learning", "algorithm"],
                    coherence_score=0.8,
                    document_count=2,
                    weight=0.7,
                    description="ML topic"
                )
            ],
            document_clusters=[
                DocumentCluster(
                    id=0,
                    name="ML Documents",
                    documents=["doc1", "doc2"],
                    centroid_keywords=["machine", "learning"],
                    similarity_threshold=0.8,
                    cluster_size=2,
                    representative_doc_id="doc1"
                )
            ],
            topic_trends=[
                TopicTrend(
                    topic_id=0,
                    topic_name="Machine Learning",
                    time_series={"2024-01-01": 0.5, "2024-01-02": 0.7},
                    trend_direction="increasing",
                    growth_rate=0.4,
                    peak_date="2024-01-02",
                    current_strength=0.7
                )
            ],
            document_topic_assignments={"doc1": [(0, 0.8)]},
            model_metadata={"n_documents": 2, "n_topics": 1}
        )
        
        with patch.object(topic_service, 'analyze_document_topics', return_value=mock_result):
            insights = await topic_service.get_topic_insights(user_id="user1")
            
            assert isinstance(insights, dict)
            assert "topic_summary" in insights
            assert "topic_distribution" in insights
            assert "cluster_analysis" in insights
            assert "trending_topics" in insights
            assert "analysis_metadata" in insights
            
            # Check topic summary
            assert insights["topic_summary"]["total_topics"] == 1
            assert insights["topic_summary"]["total_clusters"] == 1
            assert insights["topic_summary"]["most_prominent_topic"] == "Machine Learning"

    @pytest.mark.asyncio
    async def test_track_topic_modeling_event(self, topic_service, mock_db):
        """Test analytics event tracking"""
        await topic_service._track_topic_modeling_event("user1", 5, 3)
        
        # Verify analytics event was created
        assert mock_db.add.called
        assert mock_db.commit.called
        
        # Get the added event
        added_event = mock_db.add.call_args[0][0]
        assert isinstance(added_event, AnalyticsEvent)
        assert added_event.user_id == "user1"
        assert added_event.event_type == "topic_modeling_performed"
        assert added_event.event_data["n_documents"] == 5
        assert added_event.event_data["n_topics"] == 3

    @pytest.mark.asyncio
    async def test_error_handling_in_analysis(self, topic_service, mock_db):
        """Test error handling in topic analysis"""
        # Mock database error
        mock_db.query.side_effect = Exception("Database error")
        
        with pytest.raises(Exception):
            await topic_service.analyze_document_topics(user_id="user1")

    @pytest.mark.asyncio
    async def test_empty_document_content_handling(self, topic_service, mock_db, sample_documents):
        """Test handling of documents with empty content"""
        # Mock documents with empty chunks
        empty_chunks = [
            DocumentChunk(id="chunk1", document_id="doc1", content="", chunk_index=0)
        ]
        
        mock_db.query.return_value.filter.return_value.all.side_effect = [
            sample_documents[:1],  # One document
            empty_chunks  # Empty content
        ]
        
        doc_texts, doc_metadata = await topic_service._prepare_document_texts(sample_documents[:1])
        
        # Should filter out empty documents
        assert len(doc_texts) == 0
        assert len(doc_metadata) == 0

    def test_topic_info_dataclass(self):
        """Test TopicInfo dataclass"""
        topic = TopicInfo(
            id=1,
            name="Test Topic",
            keywords=["test", "topic"],
            coherence_score=0.8,
            document_count=5,
            weight=0.7,
            description="Test description"
        )
        
        assert topic.id == 1
        assert topic.name == "Test Topic"
        assert len(topic.keywords) == 2
        assert topic.coherence_score == 0.8

    def test_document_cluster_dataclass(self):
        """Test DocumentCluster dataclass"""
        cluster = DocumentCluster(
            id=1,
            name="Test Cluster",
            documents=["doc1", "doc2"],
            centroid_keywords=["test", "cluster"],
            similarity_threshold=0.8,
            cluster_size=2,
            representative_doc_id="doc1"
        )
        
        assert cluster.id == 1
        assert cluster.name == "Test Cluster"
        assert len(cluster.documents) == 2
        assert cluster.cluster_size == 2

    def test_topic_trend_dataclass(self):
        """Test TopicTrend dataclass"""
        trend = TopicTrend(
            topic_id=1,
            topic_name="Test Topic",
            time_series={"2024-01-01": 0.5},
            trend_direction="increasing",
            growth_rate=0.2,
            peak_date="2024-01-01",
            current_strength=0.5
        )
        
        assert trend.topic_id == 1
        assert trend.trend_direction == "increasing"
        assert trend.growth_rate == 0.2

if __name__ == "__main__":
    pytest.main([__file__])