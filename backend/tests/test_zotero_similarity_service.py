"""
Tests for Zotero Similarity Service
"""
import json
import pytest
import numpy as np
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from sqlalchemy.orm import Session

from services.zotero.zotero_similarity_service import ZoteroSimilarityService
from models.zotero_models import ZoteroItem, ZoteroLibrary, ZoteroConnection


class TestZoteroSimilarityService:
    """Test cases for Zotero Similarity Service"""
    
    @pytest.fixture
    def similarity_service(self):
        """Create similarity service instance"""
        return ZoteroSimilarityService()
    
    @pytest.fixture
    def mock_zotero_item(self):
        """Create mock Zotero item"""
        return ZoteroItem(
            id="item_123",
            library_id="lib_123",
            zotero_item_key="ABCD1234",
            item_type="journalArticle",
            title="Machine Learning in Academic Research",
            creators=[
                {"firstName": "John", "lastName": "Doe", "creatorType": "author"},
                {"firstName": "Jane", "lastName": "Smith", "creatorType": "author"}
            ],
            publication_title="Journal of AI Research",
            publication_year=2023,
            abstract_note="This paper explores machine learning applications in academic research.",
            tags=["machine learning", "research", "AI"],
            doi="10.1000/test.doi",
            item_metadata={}
        )
    
    @pytest.fixture
    def mock_embedding_response(self):
        """Mock embedding API response"""
        return {
            "embedding": [0.1, 0.2, 0.3, 0.4, 0.5] * 76 + [0.1, 0.2, 0.3, 0.4]  # 384 dimensions
        }
    
    @pytest.mark.asyncio
    async def test_generate_embeddings_success(
        self, similarity_service, mock_zotero_item, mock_embedding_response
    ):
        """Test successful embedding generation"""
        user_id = "user_123"
        
        # Mock dependencies
        with patch('services.zotero.zotero_similarity_service.get_db') as mock_get_db, \
             patch.object(similarity_service, '_get_user_item', return_value=mock_zotero_item), \
             patch.object(similarity_service, '_get_stored_embeddings', return_value=None), \
             patch('requests.post') as mock_post, \
             patch.object(similarity_service, '_store_embeddings') as mock_store:
            
            # Configure embedding API response
            mock_response = Mock()
            mock_response.json.return_value = mock_embedding_response
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            result = await similarity_service.generate_embeddings(
                item_id="item_123",
                user_id=user_id,
                force_regenerate=False
            )
            
            # Verify result structure
            assert result["item_id"] == "item_123"
            assert "generation_timestamp" in result
            assert "content_hash" in result
            assert "embeddings" in result
            
            # Verify embedding types
            embeddings = result["embeddings"]
            assert "semantic" in embeddings
            assert "tfidf" in embeddings
            assert "metadata" in embeddings
            
            # Verify semantic embedding
            assert len(embeddings["semantic"]) == 384
            
            # Verify TF-IDF embedding
            tfidf_emb = embeddings["tfidf"]
            assert "keywords" in tfidf_emb
            assert "frequencies" in tfidf_emb
            assert "machine" in " ".join(tfidf_emb["keywords"]).lower()
            
            # Verify metadata embedding
            metadata_emb = embeddings["metadata"]
            assert metadata_emb["item_type"] == "journalArticle"
            assert metadata_emb["publication_year"] == 2023
            assert metadata_emb["creator_count"] == 2
            
            # Verify storage was called
            mock_store.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_embeddings_item_not_found(self, similarity_service):
        """Test embedding generation when item not found"""
        user_id = "user_123"
        
        with patch('services.zotero.zotero_similarity_service.get_db'), \
             patch.object(similarity_service, '_get_user_item', return_value=None):
            
            with pytest.raises(ValueError, match="Item item_123 not found or access denied"):
                await similarity_service.generate_embeddings(
                    item_id="item_123",
                    user_id=user_id
                )
    
    @pytest.mark.asyncio
    async def test_generate_embeddings_existing_embeddings(
        self, similarity_service, mock_zotero_item
    ):
        """Test embedding generation with existing embeddings"""
        user_id = "user_123"
        existing_embeddings = {
            "item_id": "item_123",
            "generation_timestamp": "2023-01-01T00:00:00",
            "embeddings": {"semantic": [0.1, 0.2, 0.3]}
        }
        
        with patch('services.zotero.zotero_similarity_service.get_db'), \
             patch.object(similarity_service, '_get_user_item', return_value=mock_zotero_item), \
             patch.object(similarity_service, '_get_stored_embeddings', return_value=existing_embeddings):
            
            result = await similarity_service.generate_embeddings(
                item_id="item_123",
                user_id=user_id,
                force_regenerate=False
            )
            
            # Should return existing embeddings
            assert result == existing_embeddings
    
    @pytest.mark.asyncio
    async def test_generate_embeddings_no_content(self, similarity_service):
        """Test embedding generation with no content"""
        user_id = "user_123"
        
        # Create item with no content
        empty_item = ZoteroItem(
            id="item_123",
            library_id="lib_123",
            zotero_item_key="ABCD1234",
            item_type="journalArticle",
            title="",
            abstract_note="",
            creators=[],
            tags=[],
            item_metadata={}
        )
        
        with patch('services.zotero.zotero_similarity_service.get_db'), \
             patch.object(similarity_service, '_get_user_item', return_value=empty_item), \
             patch.object(similarity_service, '_get_stored_embeddings', return_value=None):
            
            result = await similarity_service.generate_embeddings(
                item_id="item_123",
                user_id=user_id
            )
            
            assert result["error"] == "No content available for embedding generation"
    
    @pytest.mark.asyncio
    async def test_find_similar_references_success(self, similarity_service):
        """Test successful similarity search"""
        user_id = "user_123"
        item_id = "item_123"
        
        # Mock target embeddings
        target_embeddings = {
            "item_id": item_id,
            "embeddings": {
                "semantic": [0.1, 0.2, 0.3, 0.4, 0.5],
                "tfidf": {"keywords": ["machine", "learning"], "frequencies": [2, 1]},
                "metadata": {"item_type": "journalArticle", "publication_year": 2023}
            }
        }
        
        # Mock candidate items
        candidate_items = [
            {
                "item_id": "item_456",
                "title": "Deep Learning Applications",
                "item_type": "journalArticle",
                "publication_year": 2022,
                "creators": [{"firstName": "Alice", "lastName": "Johnson"}],
                "embeddings": {
                    "semantic": [0.2, 0.3, 0.4, 0.5, 0.6],
                    "tfidf": {"keywords": ["deep", "learning"], "frequencies": [1, 2]},
                    "metadata": {"item_type": "journalArticle", "publication_year": 2022}
                }
            }
        ]
        
        with patch.object(similarity_service, 'generate_embeddings', return_value=target_embeddings), \
             patch.object(similarity_service, '_get_user_items_with_embeddings', return_value=candidate_items):
            
            result = await similarity_service.find_similar_references(
                item_id=item_id,
                user_id=user_id,
                similarity_types=["semantic", "tfidf", "metadata"],
                max_results=10,
                min_similarity=0.1
            )
            
            # Verify result structure
            assert result["target_item_id"] == item_id
            assert result["similarity_types"] == ["semantic", "tfidf", "metadata"]
            assert result["total_candidates"] == 1
            assert result["similar_items_found"] >= 0
            assert "similar_items" in result
            assert "analysis_timestamp" in result
    
    @pytest.mark.asyncio
    async def test_find_similar_references_no_candidates(self, similarity_service):
        """Test similarity search with no candidate items"""
        user_id = "user_123"
        item_id = "item_123"
        
        target_embeddings = {
            "item_id": item_id,
            "embeddings": {"semantic": [0.1, 0.2, 0.3]}
        }
        
        with patch.object(similarity_service, 'generate_embeddings', return_value=target_embeddings), \
             patch.object(similarity_service, '_get_user_items_with_embeddings', return_value=[]):
            
            result = await similarity_service.find_similar_references(
                item_id=item_id,
                user_id=user_id
            )
            
            assert result["total_candidates"] == 0
            assert result["similar_items_found"] == 0
            assert len(result["similar_items"]) == 0
    
    @pytest.mark.asyncio
    async def test_generate_recommendations_success(self, similarity_service):
        """Test successful recommendation generation"""
        user_id = "user_123"
        
        with patch.object(similarity_service, '_build_user_profile', return_value={"user_id": user_id}), \
             patch.object(similarity_service, '_generate_similar_recommendations', return_value=[]), \
             patch.object(similarity_service, '_generate_trending_recommendations', return_value=[]), \
             patch.object(similarity_service, '_generate_gap_filling_recommendations', return_value=[]):
            
            result = await similarity_service.generate_recommendations(
                user_id=user_id,
                library_id=None,
                recommendation_types=["similar", "trending", "gap_filling"],
                max_recommendations=10
            )
            
            # Verify result structure
            assert result["user_id"] == user_id
            assert result["recommendation_types"] == ["similar", "trending", "gap_filling"]
            assert "recommendations" in result
            assert "similar" in result["recommendations"]
            assert "trending" in result["recommendations"]
            assert "gap_filling" in result["recommendations"]
            assert "generation_timestamp" in result
    
    @pytest.mark.asyncio
    async def test_cluster_references_success(self, similarity_service):
        """Test successful reference clustering"""
        user_id = "user_123"
        
        # Mock items with embeddings
        mock_items = [
            {
                "item_id": f"item_{i}",
                "title": f"Paper {i}",
                "item_type": "journalArticle",
                "publication_year": 2023,
                "creators": [],
                "embeddings": {"semantic": [float(i), float(i+1), float(i+2)] + [0.0] * 381}
            }
            for i in range(5)
        ]
        
        with patch.object(similarity_service, '_get_user_items_with_embeddings', return_value=mock_items), \
             patch.object(similarity_service, '_extract_cluster_topics', return_value=["Topic 1", "Topic 2"]), \
             patch.object(similarity_service, '_generate_cluster_summary', return_value="Test cluster"):
            
            result = await similarity_service.cluster_references(
                user_id=user_id,
                library_id=None,
                num_clusters=2,
                clustering_method="kmeans"
            )
            
            # Verify result structure
            assert result["user_id"] == user_id
            assert result["clustering_method"] == "kmeans"
            assert result["num_clusters"] == 2
            assert result["total_items"] == 5
            assert "clusters" in result
            assert len(result["clusters"]) == 2
            assert "clustering_timestamp" in result
    
    @pytest.mark.asyncio
    async def test_cluster_references_insufficient_items(self, similarity_service):
        """Test clustering with insufficient items"""
        user_id = "user_123"
        
        # Mock insufficient items
        mock_items = [
            {
                "item_id": "item_1",
                "embeddings": {"semantic": [0.1, 0.2, 0.3]}
            }
        ]
        
        with patch.object(similarity_service, '_get_user_items_with_embeddings', return_value=mock_items):
            
            result = await similarity_service.cluster_references(
                user_id=user_id,
                clustering_method="kmeans"
            )
            
            assert "error" in result
            assert "Insufficient items for clustering" in result["error"]
    
    @pytest.mark.asyncio
    async def test_generate_semantic_embedding_success(self, similarity_service, mock_embedding_response):
        """Test semantic embedding generation"""
        content = "Machine learning and artificial intelligence research"
        
        mock_response = Mock()
        mock_response.json.return_value = mock_embedding_response
        mock_response.raise_for_status.return_value = None
        
        with patch('requests.post', return_value=mock_response):
            result = await similarity_service._generate_semantic_embedding(content)
            
            assert len(result) == 384
            assert all(isinstance(x, (int, float)) for x in result)
    
    @pytest.mark.asyncio
    async def test_generate_semantic_embedding_fallback(self, similarity_service):
        """Test semantic embedding generation with API failure"""
        content = "Machine learning research"
        
        with patch('requests.post', side_effect=Exception("API error")):
            result = await similarity_service._generate_semantic_embedding(content)
            
            # Should fallback to simple embedding
            assert len(result) == 384
            assert all(isinstance(x, (int, float)) for x in result)
    
    @pytest.mark.asyncio
    async def test_generate_tfidf_embedding(self, similarity_service, mock_zotero_item):
        """Test TF-IDF embedding generation"""
        content = "machine learning artificial intelligence research"
        
        result = await similarity_service._generate_tfidf_embedding(content, mock_zotero_item)
        
        assert "keywords" in result
        assert "frequencies" in result
        assert "total_words" in result
        assert isinstance(result["keywords"], list)
        assert isinstance(result["frequencies"], list)
    
    @pytest.mark.asyncio
    async def test_generate_metadata_embedding(self, similarity_service, mock_zotero_item):
        """Test metadata embedding generation"""
        result = await similarity_service._generate_metadata_embedding(mock_zotero_item)
        
        assert result["item_type"] == "journalArticle"
        assert result["publication_year"] == 2023
        assert result["creator_count"] == 2
        assert result["tag_count"] == 3
        assert result["has_abstract"] is True
        assert result["has_doi"] is True
        assert "creator_types" in result
        assert "creator_names" in result
    
    @pytest.mark.asyncio
    async def test_calculate_similarity_semantic(self, similarity_service):
        """Test semantic similarity calculation"""
        embedding1 = [1.0, 0.0, 0.0]
        embedding2 = [0.0, 1.0, 0.0]
        
        similarity = await similarity_service._calculate_similarity(
            embedding1, embedding2, "semantic"
        )
        
        # Should be 0 for orthogonal vectors
        assert similarity == 0.0
        
        # Test identical vectors
        similarity = await similarity_service._calculate_similarity(
            embedding1, embedding1, "semantic"
        )
        
        # Should be 1 for identical vectors
        assert similarity == 1.0
    
    @pytest.mark.asyncio
    async def test_calculate_similarity_tfidf(self, similarity_service):
        """Test TF-IDF similarity calculation"""
        embedding1 = {"keywords": ["machine", "learning", "ai"], "frequencies": [2, 1, 1]}
        embedding2 = {"keywords": ["machine", "deep", "learning"], "frequencies": [1, 1, 2]}
        
        similarity = await similarity_service._calculate_similarity(
            embedding1, embedding2, "tfidf"
        )
        
        # Should be > 0 due to shared keywords
        assert 0 < similarity <= 1
    
    @pytest.mark.asyncio
    async def test_calculate_similarity_metadata(self, similarity_service):
        """Test metadata similarity calculation"""
        embedding1 = {
            "item_type": "journalArticle",
            "publication_year": 2023,
            "creator_names": ["Doe", "Smith"],
            "publication_title": "AI Journal"
        }
        embedding2 = {
            "item_type": "journalArticle",
            "publication_year": 2022,
            "creator_names": ["Doe", "Johnson"],
            "publication_title": "AI Journal"
        }
        
        similarity = await similarity_service._calculate_similarity(
            embedding1, embedding2, "metadata"
        )
        
        # Should be > 0 due to shared characteristics
        assert 0 < similarity <= 1
    
    def test_extract_embedding_content(self, similarity_service, mock_zotero_item):
        """Test content extraction for embeddings"""
        content = similarity_service._extract_embedding_content(mock_zotero_item)
        
        assert "Machine Learning in Academic Research" in content
        assert "This paper explores machine learning" in content
        assert "John Doe Jane Smith" in content
        assert "machine learning research AI" in content
    
    def test_extract_embedding_content_minimal(self, similarity_service):
        """Test content extraction with minimal item"""
        minimal_item = ZoteroItem(
            id="item_123",
            library_id="lib_123",
            zotero_item_key="ABCD1234",
            item_type="journalArticle",
            title="Test Title",
            creators=[],
            tags=[],
            item_metadata={}
        )
        
        content = similarity_service._extract_embedding_content(minimal_item)
        assert content == "Test Title"
    
    @pytest.mark.asyncio
    async def test_store_embeddings_success(self, similarity_service):
        """Test storing embeddings"""
        mock_db = Mock(spec=Session)
        mock_item = Mock()
        mock_item.item_metadata = {}
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_item
        
        embeddings = {"test": "data"}
        
        await similarity_service._store_embeddings(
            db=mock_db,
            item_id="item_123",
            embeddings=embeddings
        )
        
        assert mock_item.item_metadata["embeddings"] == embeddings
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_store_embeddings_error(self, similarity_service):
        """Test storing embeddings with database error"""
        mock_db = Mock(spec=Session)
        mock_db.query.side_effect = Exception("Database error")
        
        embeddings = {"test": "data"}
        
        with pytest.raises(Exception):
            await similarity_service._store_embeddings(
                db=mock_db,
                item_id="item_123",
                embeddings=embeddings
            )
        
        mock_db.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_similarity_reasons(self, similarity_service):
        """Test similarity reason generation"""
        target_embeddings = {"test": "data"}
        candidate_embeddings = {"test": "data"}
        similarity_scores = {
            "semantic": 0.8,
            "tfidf": 0.6,
            "metadata": 0.4
        }
        
        reasons = await similarity_service._generate_similarity_reasons(
            target_embeddings, candidate_embeddings, similarity_scores
        )
        
        assert len(reasons) == 2  # Only scores > 0.5
        assert any("Similar content and themes" in reason for reason in reasons)
        assert any("Shared keywords and terminology" in reason for reason in reasons)