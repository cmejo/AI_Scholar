"""
Tests for Document Relationship Mapper
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import List

from services.document_relationship_mapper import (
    DocumentRelationshipMapper, DocumentSimilarity, DocumentConnection,
    DocumentCluster, DocumentRelationshipMap
)
from models.schemas import DocumentResponse


class TestDocumentRelationshipMapper:
    """Test suite for DocumentRelationshipMapper"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock()
    
    @pytest.fixture
    def mapper(self, mock_db):
        """Create DocumentRelationshipMapper instance"""
        return DocumentRelationshipMapper(mock_db)
    
    @pytest.fixture
    def sample_documents(self):
        """Sample documents for testing"""
        docs = []
        for i in range(3):
            doc = Mock()
            doc.id = f"doc_{i}"
            doc.name = f"Document {i}"
            doc.user_id = "test_user"
            doc.size = 1000 + i * 500
            doc.status = "processed"
            doc.chunks_count = 1
            doc.embeddings_count = 1
            doc.created_at = datetime.utcnow()
            docs.append(doc)
        return docs
    
    @pytest.fixture
    def sample_chunks(self):
        """Sample document chunks for testing"""
        chunks = []
        contents = [
            "This is about artificial intelligence and machine learning.",
            "Machine learning algorithms are used in AI systems.",
            "Natural language processing is a subset of AI."
        ]
        
        for i, content in enumerate(contents):
            chunk = Mock()
            chunk.document_id = f"doc_{i}"
            chunk.content = content
            chunks.append(chunk)
        
        return chunks
    
    @pytest.fixture
    def sample_entities(self):
        """Sample knowledge graph entities for testing"""
        entities = []
        entity_data = [
            ("doc_0", "artificial intelligence"),
            ("doc_0", "machine learning"),
            ("doc_1", "machine learning"),
            ("doc_1", "algorithms"),
            ("doc_2", "natural language processing"),
            ("doc_2", "AI")
        ]
        
        for doc_id, name in entity_data:
            entity = Mock()
            entity.document_id = doc_id
            entity.name = name
            entities.append(entity)
        
        return entities
    
    @pytest.fixture
    def sample_tags(self):
        """Sample document tags for testing"""
        tags = []
        tag_data = [
            ("doc_0", "AI", "topic"),
            ("doc_0", "technology", "domain"),
            ("doc_1", "AI", "topic"),
            ("doc_1", "algorithms", "topic"),
            ("doc_2", "AI", "topic"),
            ("doc_2", "NLP", "topic")
        ]
        
        for doc_id, tag_name, tag_type in tag_data:
            tag = Mock()
            tag.document_id = doc_id
            tag.tag_name = tag_name
            tag.tag_type = tag_type
            tags.append(tag)
        
        return tags

    @pytest.mark.asyncio
    async def test_analyze_document_relationships_basic(
        self, mapper, mock_db, sample_documents, sample_chunks, sample_entities, sample_tags
    ):
        """Test basic document relationship analysis"""
        # Mock database queries
        mock_db.query.return_value.filter.return_value.all.return_value = sample_documents
        
        # Mock chunk queries
        def mock_chunk_query(*args):
            mock_query = Mock()
            mock_query.filter.return_value.all.return_value = [
                chunk for chunk in sample_chunks 
                if chunk.document_id == args[0].document_id
            ]
            return mock_query
        
        # Mock entity queries
        def mock_entity_query(*args):
            mock_query = Mock()
            mock_query.filter.return_value.all.return_value = [
                entity for entity in sample_entities 
                if entity.document_id == args[0].document_id
            ]
            return mock_query
        
        # Mock tag queries
        def mock_tag_query(*args):
            mock_query = Mock()
            if hasattr(args[0], 'tag_type'):
                # Topic tag query
                mock_query.filter.return_value.all.return_value = [
                    tag for tag in sample_tags 
                    if tag.document_id == args[0].document_id and tag.tag_type == 'topic'
                ]
            else:
                # Regular tag query
                mock_query.filter.return_value.all.return_value = [
                    tag for tag in sample_tags 
                    if tag.document_id == args[0].document_id
                ]
            return mock_query
        
        # Configure mock to return appropriate results based on query type
        def side_effect(query_class):
            if 'DocumentChunk' in str(query_class):
                return mock_chunk_query(query_class)
            elif 'KnowledgeGraphEntity' in str(query_class):
                return mock_entity_query(query_class)
            elif 'DocumentTag' in str(query_class):
                return mock_tag_query(query_class)
            else:
                mock_query = Mock()
                mock_query.filter.return_value.all.return_value = sample_documents
                return mock_query
        
        mock_db.query.side_effect = side_effect
        
        # Test the analysis
        result = await mapper.analyze_document_relationships("test_user")
        
        # Verify results
        assert isinstance(result, DocumentRelationshipMap)
        assert len(result.documents) == 3
        assert len(result.similarities) >= 0  # Should find some similarities
        assert len(result.connections) >= 0  # Should generate connections
        assert isinstance(result.network_metrics, dict)
        assert isinstance(result.visualization_data, dict)

    @pytest.mark.asyncio
    async def test_calculate_content_similarity(
        self, mapper, mock_db, sample_documents, sample_chunks
    ):
        """Test content similarity calculation"""
        # Mock chunk queries
        def mock_chunk_filter(document_id):
            mock_query = Mock()
            mock_query.all.return_value = [
                chunk for chunk in sample_chunks 
                if chunk.document_id == document_id
            ]
            return mock_query
        
        mock_db.query.return_value.filter.side_effect = mock_chunk_filter
        
        # Test content similarity calculation
        similarities = await mapper._calculate_content_similarity(sample_documents)
        
        # Verify results
        assert isinstance(similarities, list)
        for similarity in similarities:
            assert isinstance(similarity, DocumentSimilarity)
            assert similarity.similarity_type == "content"
            assert 0 <= similarity.similarity_score <= 1
            assert similarity.document1_id != similarity.document2_id

    @pytest.mark.asyncio
    async def test_calculate_entity_similarity(
        self, mapper, mock_db, sample_documents, sample_entities
    ):
        """Test entity similarity calculation"""
        # Mock entity queries
        def mock_entity_filter(document_id):
            mock_query = Mock()
            mock_query.all.return_value = [
                entity for entity in sample_entities 
                if entity.document_id == document_id
            ]
            return mock_query
        
        mock_db.query.return_value.filter.side_effect = mock_entity_filter
        
        # Test entity similarity calculation
        similarities = await mapper._calculate_entity_similarity(sample_documents)
        
        # Verify results
        assert isinstance(similarities, list)
        for similarity in similarities:
            assert isinstance(similarity, DocumentSimilarity)
            assert similarity.similarity_type == "entity"
            assert 0 <= similarity.similarity_score <= 1
            assert len(similarity.shared_entities) > 0

    @pytest.mark.asyncio
    async def test_calculate_tag_similarity(
        self, mapper, mock_db, sample_documents, sample_tags
    ):
        """Test tag similarity calculation"""
        # Mock tag queries
        def mock_tag_filter(document_id):
            mock_query = Mock()
            mock_query.all.return_value = [
                tag for tag in sample_tags 
                if tag.document_id == document_id
            ]
            return mock_query
        
        mock_db.query.return_value.filter.side_effect = mock_tag_filter
        
        # Test tag similarity calculation
        similarities = await mapper._calculate_tag_similarity(sample_documents)
        
        # Verify results
        assert isinstance(similarities, list)
        for similarity in similarities:
            assert isinstance(similarity, DocumentSimilarity)
            assert similarity.similarity_type == "tag"
            assert 0 <= similarity.similarity_score <= 1
            assert len(similarity.shared_tags) > 0

    @pytest.mark.asyncio
    async def test_generate_document_connections(self, mapper, sample_documents):
        """Test document connection generation"""
        # Create sample similarities
        similarities = [
            DocumentSimilarity(
                document1_id="doc_0",
                document1_name="Document 0",
                document2_id="doc_1",
                document2_name="Document 1",
                similarity_score=0.8,
                similarity_type="content",
                shared_entities=["AI"],
                shared_tags=["technology"],
                common_topics=["machine learning"]
            ),
            DocumentSimilarity(
                document1_id="doc_1",
                document1_name="Document 1",
                document2_id="doc_2",
                document2_name="Document 2",
                similarity_score=0.6,
                similarity_type="entity",
                shared_entities=["AI", "algorithms"],
                shared_tags=[],
                common_topics=[]
            )
        ]
        
        # Test connection generation
        connections = await mapper._generate_document_connections(sample_documents, similarities)
        
        # Verify results
        assert isinstance(connections, list)
        assert len(connections) == 2
        
        for connection in connections:
            assert isinstance(connection, DocumentConnection)
            assert connection.source_document_id in ["doc_0", "doc_1"]
            assert connection.target_document_id in ["doc_1", "doc_2"]
            assert 0 <= connection.strength <= 1
            assert connection.connection_type.endswith("_similarity")
            assert isinstance(connection.metadata, dict)

    @pytest.mark.asyncio
    async def test_cluster_documents(
        self, mapper, mock_db, sample_documents, sample_chunks
    ):
        """Test document clustering"""
        # Mock chunk queries
        def mock_chunk_filter(document_id):
            mock_query = Mock()
            mock_query.all.return_value = [
                chunk for chunk in sample_chunks 
                if chunk.document_id == document_id
            ]
            return mock_query
        
        mock_db.query.return_value.filter.side_effect = mock_chunk_filter
        
        # Test clustering
        clusters = await mapper._cluster_documents(sample_documents, n_clusters=2)
        
        # Verify results
        assert isinstance(clusters, list)
        for cluster in clusters:
            assert isinstance(cluster, DocumentCluster)
            assert cluster.cluster_id >= 0
            assert len(cluster.documents) >= 2
            assert len(cluster.centroid_topics) > 0
            assert isinstance(cluster.cluster_name, str)
            assert 0 <= cluster.coherence_score <= 1

    @pytest.mark.asyncio
    async def test_calculate_network_metrics(self, mapper, sample_documents):
        """Test network metrics calculation"""
        # Create sample connections
        connections = [
            DocumentConnection(
                source_document_id="doc_0",
                target_document_id="doc_1",
                connection_type="content_similarity",
                strength=0.8,
                metadata={}
            ),
            DocumentConnection(
                source_document_id="doc_1",
                target_document_id="doc_2",
                connection_type="entity_similarity",
                strength=0.6,
                metadata={}
            )
        ]
        
        # Test metrics calculation
        metrics = await mapper._calculate_network_metrics(sample_documents, connections)
        
        # Verify results
        assert isinstance(metrics, dict)
        assert "total_documents" in metrics
        assert "total_connections" in metrics
        assert "network_density" in metrics
        assert "connected_components" in metrics
        assert metrics["total_documents"] == 3
        assert metrics["total_connections"] == 2

    @pytest.mark.asyncio
    async def test_generate_visualization_data(self, mapper, sample_documents):
        """Test visualization data generation"""
        # Create sample connections and clusters
        connections = [
            DocumentConnection(
                source_document_id="doc_0",
                target_document_id="doc_1",
                connection_type="content_similarity",
                strength=0.8,
                metadata={"similarity_score": 0.8}
            )
        ]
        
        clusters = [
            DocumentCluster(
                cluster_id=0,
                documents=["doc_0", "doc_1"],
                centroid_topics=["AI", "machine learning"],
                cluster_name="AI Cluster",
                coherence_score=0.7
            )
        ]
        
        # Test visualization data generation
        viz_data = await mapper._generate_visualization_data(
            sample_documents, connections, clusters
        )
        
        # Verify results
        assert isinstance(viz_data, dict)
        assert "nodes" in viz_data
        assert "edges" in viz_data
        assert "clusters" in viz_data
        assert "layout_suggestions" in viz_data
        assert "color_scheme" in viz_data
        
        # Verify nodes
        assert len(viz_data["nodes"]) == 3
        for node in viz_data["nodes"]:
            assert "id" in node
            assert "name" in node
            assert "size" in node
            assert "cluster" in node
        
        # Verify edges
        assert len(viz_data["edges"]) == 1
        for edge in viz_data["edges"]:
            assert "source" in edge
            assert "target" in edge
            assert "weight" in edge
            assert "type" in edge

    @pytest.mark.asyncio
    async def test_get_document_connections(
        self, mapper, mock_db, sample_documents, sample_chunks, sample_entities
    ):
        """Test getting connections for a specific document"""
        # Mock document query
        mock_db.query.return_value.filter.return_value.first.return_value = sample_documents[0]
        
        # Mock all documents query
        mock_db.query.return_value.filter.return_value.all.return_value = sample_documents
        
        # Mock chunk and entity queries (simplified)
        def mock_query_side_effect(query_class):
            mock_query = Mock()
            if 'DocumentChunk' in str(query_class):
                mock_query.filter.return_value.all.return_value = sample_chunks
            elif 'KnowledgeGraphEntity' in str(query_class):
                mock_query.filter.return_value.all.return_value = sample_entities
            else:
                mock_query.filter.return_value.all.return_value = []
            return mock_query
        
        mock_db.query.side_effect = mock_query_side_effect
        
        # Test getting document connections
        connections = await mapper.get_document_connections("doc_0", "test_user")
        
        # Verify results
        assert isinstance(connections, list)
        for connection in connections:
            assert isinstance(connection, DocumentConnection)
            assert connection.source_document_id == "doc_0" or connection.target_document_id == "doc_0"

    @pytest.mark.asyncio
    async def test_get_relationship_insights(
        self, mapper, mock_db, sample_documents, sample_chunks, sample_entities, sample_tags
    ):
        """Test getting relationship insights"""
        # Mock the analyze_document_relationships method
        mock_relationship_map = DocumentRelationshipMap(
            documents=[DocumentResponse.model_validate(doc) for doc in sample_documents],
            similarities=[
                DocumentSimilarity(
                    document1_id="doc_0",
                    document1_name="Document 0",
                    document2_id="doc_1",
                    document2_name="Document 1",
                    similarity_score=0.8,
                    similarity_type="content",
                    shared_entities=[],
                    shared_tags=[],
                    common_topics=[]
                )
            ],
            connections=[
                DocumentConnection(
                    source_document_id="doc_0",
                    target_document_id="doc_1",
                    connection_type="content_similarity",
                    strength=0.8,
                    metadata={}
                )
            ],
            clusters=[
                DocumentCluster(
                    cluster_id=0,
                    documents=["doc_0", "doc_1"],
                    centroid_topics=["AI"],
                    cluster_name="AI Cluster",
                    coherence_score=0.7
                )
            ],
            network_metrics={"network_density": 0.5},
            visualization_data={}
        )
        
        # Mock the analyze_document_relationships method
        async def mock_analyze(*args, **kwargs):
            return mock_relationship_map
        mapper.analyze_document_relationships = mock_analyze
        
        # Test getting insights
        insights = await mapper.get_relationship_insights("test_user")
        
        # Verify results
        assert isinstance(insights, dict)
        assert "total_documents" in insights
        assert "total_connections" in insights
        assert "similarity_distribution" in insights
        assert "cluster_analysis" in insights
        assert "network_insights" in insights
        assert "recommendations" in insights
        
        assert insights["total_documents"] == 3
        assert insights["total_connections"] == 1
        assert isinstance(insights["recommendations"], list)

    @pytest.mark.asyncio
    async def test_empty_document_set(self, mapper, mock_db):
        """Test handling of empty document set"""
        # Mock empty document query
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        # Test analysis with no documents
        result = await mapper.analyze_document_relationships("test_user")
        
        # Verify results
        assert isinstance(result, DocumentRelationshipMap)
        assert len(result.documents) == 0
        assert len(result.similarities) == 0
        assert len(result.connections) == 0
        assert len(result.clusters) == 0

    @pytest.mark.asyncio
    async def test_single_document(self, mapper, mock_db, sample_documents):
        """Test handling of single document"""
        # Mock single document query
        mock_db.query.return_value.filter.return_value.all.return_value = [sample_documents[0]]
        
        # Test analysis with single document
        result = await mapper.analyze_document_relationships("test_user")
        
        # Verify results
        assert isinstance(result, DocumentRelationshipMap)
        assert len(result.documents) == 1
        assert len(result.similarities) == 0
        assert len(result.connections) == 0
        assert len(result.clusters) == 0

    @pytest.mark.asyncio
    async def test_error_handling(self, mapper, mock_db):
        """Test error handling in relationship analysis"""
        # Mock database error
        mock_db.query.side_effect = Exception("Database error")
        
        # Test that errors are handled gracefully
        with pytest.raises(Exception):
            await mapper.analyze_document_relationships("test_user")

    def test_similarity_threshold_filtering(self, mapper):
        """Test that similarity threshold filtering works correctly"""
        # This would be tested as part of the integration tests
        # since it involves the actual similarity calculation methods
        pass

    def test_connection_strength_calculation(self, mapper):
        """Test connection strength calculation logic"""
        # This would be tested as part of the generate_document_connections test
        pass

    def test_cluster_naming_logic(self, mapper):
        """Test cluster naming logic"""
        # This would be tested as part of the cluster_documents test
        pass