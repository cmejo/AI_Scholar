"""
Tests for Adaptive Retrieval System

Tests the personalized search functionality, ranking algorithms,
and optimization capabilities of the adaptive retrieval system.
"""
import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.orm import Session

from services.adaptive_retrieval import AdaptiveRetriever, RetrievalOptimizer
from services.user_profile_service import UserProfileManager
from models.schemas import PersonalizationSettings, UserPreferences, UserProfileResponse
from core.database import UserProfile, DocumentTag, AnalyticsEvent, Message

class TestAdaptiveRetriever:
    """Test cases for AdaptiveRetriever class."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_vector_store(self):
        """Mock vector store service."""
        mock = Mock()
        mock.semantic_search = AsyncMock()
        return mock
    
    @pytest.fixture
    def mock_profile_manager(self):
        """Mock user profile manager."""
        mock = Mock(spec=UserProfileManager)
        mock.get_user_profile = AsyncMock()
        mock.get_personalization_weights = AsyncMock()
        return mock
    
    @pytest.fixture
    def adaptive_retriever(self, mock_db):
        """Create AdaptiveRetriever instance with mocked dependencies."""
        retriever = AdaptiveRetriever(mock_db)
        return retriever
    
    @pytest.fixture
    def sample_user_profile(self):
        """Sample user profile for testing."""
        return UserProfileResponse(
            id="profile-1",
            user_id="user-1",
            preferences=UserPreferences(
                response_style="detailed",
                domain_focus=["technology", "science"],
                citation_preference="inline"
            ),
            interaction_history={
                "total_queries": 50,
                "query_history": [
                    {
                        "timestamp": datetime.utcnow().isoformat(),
                        "query": "machine learning algorithms",
                        "satisfaction": 4.5
                    }
                ]
            },
            domain_expertise={"technology": 0.8, "science": 0.6},
            learning_style="visual",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    @pytest.fixture
    def sample_search_results(self):
        """Sample search results for testing."""
        return [
            {
                "id": "doc1_chunk1",
                "content": "Machine learning is a subset of artificial intelligence...",
                "metadata": {
                    "document_id": "doc1",
                    "document_name": "AI Fundamentals",
                    "chunk_index": 1,
                    "content_length": 500
                },
                "relevance": 0.9,
                "distance": 0.1
            },
            {
                "id": "doc2_chunk1",
                "content": "Deep learning algorithms require large datasets...",
                "metadata": {
                    "document_id": "doc2",
                    "document_name": "Deep Learning Guide",
                    "chunk_index": 1,
                    "content_length": 750
                },
                "relevance": 0.8,
                "distance": 0.2
            },
            {
                "id": "doc3_chunk1",
                "content": "Statistical analysis methods in research...",
                "metadata": {
                    "document_id": "doc3",
                    "document_name": "Statistics Manual",
                    "chunk_index": 1,
                    "content_length": 400
                },
                "relevance": 0.7,
                "distance": 0.3
            }
        ]
    
    @pytest.mark.asyncio
    async def test_personalized_search_with_profile(
        self, 
        adaptive_retriever, 
        sample_user_profile, 
        sample_search_results
    ):
        """Test personalized search with existing user profile."""
        # Mock dependencies
        with patch.object(adaptive_retriever, 'profile_manager') as mock_profile_manager, \
             patch.object(adaptive_retriever, 'vector_store') as mock_vector_store:
            
            mock_profile_manager.get_user_profile.return_value = sample_user_profile
            mock_profile_manager.get_personalization_weights.return_value = {
                "domain_weights": {"technology": 0.8, "science": 0.6},
                "complexity_preference": 0.7,
                "satisfaction_weight": 0.8
            }
            mock_vector_store.semantic_search.return_value = sample_search_results
            
            # Mock database queries for domain boost calculation
            mock_tags = [
                Mock(tag_name="technology", confidence_score=0.9, tag_type="domain"),
                Mock(tag_name="science", confidence_score=0.7, tag_type="topic")
            ]
            adaptive_retriever.db.query.return_value.filter.return_value.all.return_value = mock_tags
            
            # Mock analytics event creation
            adaptive_retriever.db.add = Mock()
            adaptive_retriever.db.commit = Mock()
            
            # Test personalized search
            results = await adaptive_retriever.personalized_search(
                query="machine learning algorithms",
                user_id="user-1",
                limit=5,
                personalization_level=1.0
            )
            
            # Assertions
            assert len(results) <= 5
            assert all("personalized_score" in result for result in results)
            assert all("personalization_factors" in result for result in results)
            
            # Check that results are sorted by personalized score
            scores = [result["personalized_score"] for result in results]
            assert scores == sorted(scores, reverse=True)
            
            # Verify profile manager was called
            mock_profile_manager.get_user_profile.assert_called_once_with("user-1")
            mock_profile_manager.get_personalization_weights.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_personalized_search_without_profile(self, adaptive_retriever, sample_search_results):
        """Test personalized search fallback when no user profile exists."""
        with patch.object(adaptive_retriever, 'profile_manager') as mock_profile_manager, \
             patch.object(adaptive_retriever, 'vector_store') as mock_vector_store:
            
            mock_profile_manager.get_user_profile.return_value = None
            mock_vector_store.semantic_search.return_value = sample_search_results
            
            results = await adaptive_retriever.personalized_search(
                query="test query",
                user_id="user-1",
                limit=5
            )
            
            # Should fallback to basic search
            assert results == sample_search_results
            mock_vector_store.semantic_search.assert_called_with("test query", "user-1", 5)
    
    @pytest.mark.asyncio
    async def test_personalized_search_with_zero_personalization(
        self, 
        adaptive_retriever, 
        sample_user_profile, 
        sample_search_results
    ):
        """Test personalized search with personalization disabled."""
        with patch.object(adaptive_retriever, 'profile_manager') as mock_profile_manager, \
             patch.object(adaptive_retriever, 'vector_store') as mock_vector_store:
            
            mock_profile_manager.get_user_profile.return_value = sample_user_profile
            mock_vector_store.semantic_search.return_value = sample_search_results
            
            results = await adaptive_retriever.personalized_search(
                query="test query",
                user_id="user-1",
                limit=5,
                personalization_level=0.0
            )
            
            # Should return basic results without personalization
            assert results == sample_search_results[:5]
    
    @pytest.mark.asyncio
    async def test_get_personalization_weights(self, adaptive_retriever, sample_user_profile):
        """Test personalization weights calculation."""
        with patch.object(adaptive_retriever, 'profile_manager') as mock_profile_manager:
            mock_profile_manager.get_personalization_weights.return_value = {
                "domain_weights": {"technology": 0.8},
                "complexity_preference": 0.7,
                "satisfaction_weight": 0.8
            }
            
            # Mock historical performance data
            adaptive_retriever.db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
            
            weights = await adaptive_retriever._get_personalization_weights(
                "user-1", "machine learning", sample_user_profile
            )
            
            assert "domain_preference" in weights
            assert "complexity_preference" in weights
            assert "source_quality_weight" in weights
            assert isinstance(weights["domain_preference"], dict)
    
    @pytest.mark.asyncio
    async def test_analyze_query_context(self, adaptive_retriever):
        """Test query context analysis."""
        # Test technology domain query
        tech_context = await adaptive_retriever._analyze_query_context(
            "machine learning algorithm implementation", "user-1"
        )
        
        assert "domain_signals" in tech_context
        assert "technology" in tech_context["domain_signals"]
        assert tech_context["domain_signals"]["technology"] > 0
        assert tech_context["question_type"] == "informational"
        
        # Test how-to query
        howto_context = await adaptive_retriever._analyze_query_context(
            "how to implement neural networks", "user-1"
        )
        
        assert howto_context["question_type"] == "procedural"
        assert "instructional" in howto_context["content_type_signals"]
    
    def test_classify_question_type(self, adaptive_retriever):
        """Test question type classification."""
        assert adaptive_retriever._classify_question_type("What is machine learning?") == "definitional"
        assert adaptive_retriever._classify_question_type("How to train a model?") == "procedural"
        assert adaptive_retriever._classify_question_type("Why does overfitting occur?") == "causal"
        assert adaptive_retriever._classify_question_type("Compare CNN and RNN") == "comparative"
        assert adaptive_retriever._classify_question_type("Is this correct?") == "interrogative"
        assert adaptive_retriever._classify_question_type("Machine learning overview") == "informational"
    
    @pytest.mark.asyncio
    async def test_apply_personalized_ranking(self, adaptive_retriever, sample_search_results):
        """Test personalized ranking application."""
        weights = {
            "domain_preference": {"technology": 0.8},
            "interaction_boost": {"doc1": 0.1},
            "content_type_preference": {"practical": 0.7},
            "recency_preference": 0.6,
            "complexity_preference": 0.7,
            "source_quality_weight": 0.8,
            "feedback_adjustment": 1.0
        }
        
        # Mock domain boost calculation
        with patch.object(adaptive_retriever, '_calculate_domain_boost', return_value=0.1):
            results = await adaptive_retriever._apply_personalized_ranking(
                sample_search_results, "test query", "user-1", weights, 1.0
            )
            
            assert len(results) == len(sample_search_results)
            assert all("personalized_score" in result for result in results)
            assert all("personalization_factors" in result for result in results)
            
            # Check sorting by personalized score
            scores = [result["personalized_score"] for result in results]
            assert scores == sorted(scores, reverse=True)
    
    @pytest.mark.asyncio
    async def test_calculate_domain_boost(self, adaptive_retriever):
        """Test domain boost calculation."""
        domain_preferences = {"technology": 0.8, "science": 0.6}
        
        # Mock document tags
        mock_tags = [
            Mock(tag_name="technology", confidence_score=0.9, tag_type="domain"),
            Mock(tag_name="science", confidence_score=0.7, tag_type="topic")
        ]
        adaptive_retriever.db.query.return_value.filter.return_value.all.return_value = mock_tags
        
        boost = await adaptive_retriever._calculate_domain_boost(
            "doc1", domain_preferences, {}
        )
        
        assert boost > 0
        assert isinstance(boost, float)
    
    def test_calculate_content_type_boost(self, adaptive_retriever):
        """Test content type boost calculation."""
        result = {
            "content": "This is a practical example of machine learning implementation with tutorial steps"
        }
        content_preferences = {"practical": 0.8, "instructional": 0.9}
        
        boost = adaptive_retriever._calculate_content_type_boost(result, content_preferences)
        
        assert boost > 0
        assert boost <= 0.2  # Should be capped at 20%
    
    def test_calculate_complexity_boost(self, adaptive_retriever):
        """Test complexity boost calculation."""
        # High complexity content
        complex_result = {
            "content": "Advanced algorithm implementation with sophisticated architecture and complex methodology framework"
        }
        
        boost_high = adaptive_retriever._calculate_complexity_boost(complex_result, 0.8)
        boost_low = adaptive_retriever._calculate_complexity_boost(complex_result, 0.2)
        
        assert boost_high > boost_low  # Higher preference should give higher boost
        assert -0.1 <= boost_high <= 0.1  # Should be within expected range
    
    @pytest.mark.asyncio
    async def test_apply_domain_adaptation(self, adaptive_retriever, sample_search_results, sample_user_profile):
        """Test domain adaptation application."""
        # Mock document tags for domain adaptation
        mock_tag = Mock(tag_name="technology", confidence_score=0.9, tag_type="domain")
        adaptive_retriever.db.query.return_value.filter.return_value.first.return_value = mock_tag
        
        adapted_results = await adaptive_retriever._apply_domain_adaptation(
            sample_search_results, "user-1", sample_user_profile
        )
        
        assert len(adapted_results) == len(sample_search_results)
        
        # Check if domain adaptation was applied
        tech_results = [r for r in adapted_results if r.get("domain_adapted")]
        assert len(tech_results) > 0  # At least one result should be domain-adapted
    
    @pytest.mark.asyncio
    async def test_learn_from_search(self, adaptive_retriever, sample_search_results):
        """Test learning from search interactions."""
        adaptive_retriever.db.add = Mock()
        adaptive_retriever.db.commit = Mock()
        
        # Mock domain extraction
        with patch.object(adaptive_retriever, '_extract_top_domains', return_value=["technology", "science"]):
            await adaptive_retriever._learn_from_search(
                "user-1", "machine learning", sample_search_results
            )
            
            # Verify analytics event was created
            adaptive_retriever.db.add.assert_called_once()
            adaptive_retriever.db.commit.assert_called_once()
            
            # Check the analytics event
            call_args = adaptive_retriever.db.add.call_args[0][0]
            assert call_args.user_id == "user-1"
            assert call_args.event_type == "adaptive_search"
            assert "query" in call_args.event_data
    
    @pytest.mark.asyncio
    async def test_get_personalization_stats(self, adaptive_retriever):
        """Test personalization statistics retrieval."""
        # Mock analytics events
        mock_events = [
            Mock(
                event_data={
                    "personalization_applied": True,
                    "results_count": 5,
                    "top_domains": ["technology", "science"]
                }
            ),
            Mock(
                event_data={
                    "personalization_applied": False,
                    "results_count": 3,
                    "top_domains": ["business"]
                }
            )
        ]
        adaptive_retriever.db.query.return_value.filter.return_value.all.return_value = mock_events
        
        stats = await adaptive_retriever.get_personalization_stats("user-1")
        
        assert "total_searches" in stats
        assert "personalized_searches" in stats
        assert "personalization_rate" in stats
        assert "top_domains" in stats
        assert stats["total_searches"] == 2
        assert stats["personalized_searches"] == 1
        assert stats["personalization_rate"] == 0.5

class TestRetrievalOptimizer:
    """Test cases for RetrievalOptimizer class."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def retrieval_optimizer(self, mock_db):
        """Create RetrievalOptimizer instance."""
        return RetrievalOptimizer(mock_db)
    
    @pytest.fixture
    def sample_feedback_data(self):
        """Sample feedback data for testing."""
        return [
            {
                "rating": 5,
                "domains": ["technology", "ai"],
                "query": "machine learning algorithms",
                "timestamp": datetime.utcnow().isoformat()
            },
            {
                "rating": 2,
                "domains": ["business", "finance"],
                "query": "market analysis",
                "timestamp": datetime.utcnow().isoformat()
            },
            {
                "rating": 4,
                "domains": ["technology", "programming"],
                "query": "python programming",
                "timestamp": datetime.utcnow().isoformat()
            }
        ]
    
    @pytest.mark.asyncio
    async def test_optimize_for_user_high_confidence(
        self, 
        retrieval_optimizer, 
        sample_feedback_data
    ):
        """Test optimization with high confidence recommendations."""
        # Mock user profile
        mock_profile = Mock()
        mock_profile.domain_expertise = {"technology": 0.6}
        
        with patch.object(retrieval_optimizer.adaptive_retriever, 'profile_manager') as mock_profile_manager:
            mock_profile_manager.get_user_profile.return_value = mock_profile
            
            # Mock optimization methods
            with patch.object(retrieval_optimizer, '_generate_optimization_recommendations') as mock_gen_rec, \
                 patch.object(retrieval_optimizer, '_apply_optimizations') as mock_apply:
                
                mock_gen_rec.return_value = {
                    "domain_weight_adjustments": {"technology": 0.1},
                    "confidence": 0.8
                }
                
                result = await retrieval_optimizer.optimize_for_user("user-1", sample_feedback_data)
                
                assert result["optimizations_applied"] is True
                assert result["confidence"] == 0.8
                mock_apply.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_optimize_for_user_low_confidence(
        self, 
        retrieval_optimizer, 
        sample_feedback_data
    ):
        """Test optimization with low confidence recommendations."""
        mock_profile = Mock()
        mock_profile.domain_expertise = {"technology": 0.6}
        
        with patch.object(retrieval_optimizer.adaptive_retriever, 'profile_manager') as mock_profile_manager:
            mock_profile_manager.get_user_profile.return_value = mock_profile
            
            with patch.object(retrieval_optimizer, '_generate_optimization_recommendations') as mock_gen_rec, \
                 patch.object(retrieval_optimizer, '_apply_optimizations') as mock_apply:
                
                mock_gen_rec.return_value = {
                    "domain_weight_adjustments": {"technology": 0.05},
                    "confidence": 0.3
                }
                
                result = await retrieval_optimizer.optimize_for_user("user-1", sample_feedback_data)
                
                assert result["optimizations_applied"] is False
                assert result["confidence"] == 0.3
                mock_apply.assert_not_called()
    
    def test_analyze_feedback_patterns(self, retrieval_optimizer, sample_feedback_data):
        """Test feedback pattern analysis."""
        analysis = retrieval_optimizer._analyze_feedback_patterns(sample_feedback_data)
        
        assert "avg_rating" in analysis
        assert "total_feedback" in analysis
        assert "preferred_domains" in analysis
        assert "avoided_domains" in analysis
        assert "satisfaction_trend" in analysis
        
        assert analysis["total_feedback"] == 3
        assert analysis["avg_rating"] == (5 + 2 + 4) / 3
        
        # Check domain preferences
        preferred_domains = dict(analysis["preferred_domains"])
        assert "technology" in preferred_domains
        assert preferred_domains["technology"] == 2  # Appears in 2 high-rated items
    
    @pytest.mark.asyncio
    async def test_generate_optimization_recommendations(self, retrieval_optimizer):
        """Test optimization recommendation generation."""
        feedback_analysis = {
            "avg_rating": 2.0,  # Low satisfaction
            "preferred_domains": [("technology", 3), ("science", 2)],
            "avoided_domains": [("business", 2)],
            "satisfaction_trend": "declining"
        }
        
        mock_profile = Mock()
        mock_profile.domain_expertise = {"technology": 0.5}
        
        recommendations = await retrieval_optimizer._generate_optimization_recommendations(
            feedback_analysis, mock_profile
        )
        
        assert "domain_weight_adjustments" in recommendations
        assert "personalization_level_adjustment" in recommendations
        assert "confidence" in recommendations
        
        # Should recommend increasing technology weight
        assert recommendations["domain_weight_adjustments"]["technology"] == 0.1
        # Should recommend decreasing business weight
        assert recommendations["domain_weight_adjustments"]["business"] == -0.1
        # Should recommend increasing personalization due to low satisfaction
        assert recommendations["personalization_level_adjustment"] == 0.2
    
    @pytest.mark.asyncio
    async def test_apply_optimizations(self, retrieval_optimizer):
        """Test optimization application."""
        recommendations = {
            "domain_weight_adjustments": {"technology": 0.1, "business": -0.1},
            "personalization_level_adjustment": 0.2
        }
        
        mock_profile = Mock()
        mock_profile.domain_expertise = {"technology": 0.5, "business": 0.6}
        
        with patch.object(retrieval_optimizer.adaptive_retriever, 'profile_manager') as mock_profile_manager:
            mock_profile_manager.get_user_profile.return_value = mock_profile
            mock_profile_manager.track_user_interaction = AsyncMock()
            
            await retrieval_optimizer._apply_optimizations("user-1", recommendations)
            
            # Verify interaction tracking was called
            mock_profile_manager.track_user_interaction.assert_called_once()
            call_args = mock_profile_manager.track_user_interaction.call_args
            assert call_args[1]["user_id"] == "user-1"
            assert call_args[1]["interaction_type"] == "optimization"

class TestIntegration:
    """Integration tests for adaptive retrieval system."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_personalized_search(self):
        """Test complete personalized search workflow."""
        # This would require a more complex setup with actual database
        # and vector store instances. For now, we'll test the main flow
        # with mocked dependencies.
        
        mock_db = Mock(spec=Session)
        retriever = AdaptiveRetriever(mock_db)
        
        # Mock all dependencies
        with patch.object(retriever, 'profile_manager') as mock_profile_manager, \
             patch.object(retriever, 'vector_store') as mock_vector_store:
            
            # Setup mocks
            mock_profile = Mock()
            mock_profile.domain_expertise = {"technology": 0.8}
            mock_profile.preferences = {"response_style": "detailed"}
            mock_profile_manager.get_user_profile.return_value = mock_profile
            mock_profile_manager.get_personalization_weights.return_value = {
                "domain_weights": {"technology": 0.8}
            }
            
            mock_vector_store.semantic_search.return_value = [
                {
                    "id": "test_chunk",
                    "content": "Test content about machine learning",
                    "metadata": {"document_id": "test_doc", "document_name": "Test Doc"},
                    "relevance": 0.8
                }
            ]
            
            # Mock database queries
            mock_db.query.return_value.filter.return_value.all.return_value = []
            mock_db.add = Mock()
            mock_db.commit = Mock()
            
            # Execute personalized search
            results = await retriever.personalized_search(
                query="machine learning algorithms",
                user_id="test_user",
                limit=5,
                personalization_level=1.0
            )
            
            # Verify results
            assert len(results) > 0
            assert "personalized_score" in results[0]
            
            # Verify learning was triggered
            mock_db.add.assert_called()
            mock_db.commit.assert_called()

if __name__ == "__main__":
    pytest.main([__file__])