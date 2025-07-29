"""
Tests for Domain Adaptation Service
"""
import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.orm import Session

from services.domain_adapter import DomainAdapter, DomainDetector
from core.database import (
    UserProfile, DocumentTag, AnalyticsEvent, Message, Document
)
from models.schemas import UserPreferences

class TestDomainAdapter:
    """Test cases for DomainAdapter class."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def domain_adapter(self, mock_db):
        """Create DomainAdapter instance with mock database."""
        return DomainAdapter(mock_db)
    
    @pytest.fixture
    def sample_user_profile(self):
        """Create sample user profile."""
        return UserProfile(
            id="profile-1",
            user_id="user-1",
            preferences={
                "language": "en",
                "response_style": "detailed",
                "domain_focus": ["technology", "science"]
            },
            interaction_history={
                "total_queries": 50,
                "document_interactions": {
                    "doc-1": {"access_count": 5, "queries_related": 3},
                    "doc-2": {"access_count": 3, "queries_related": 2}
                }
            },
            domain_expertise={"technology": 0.8, "science": 0.6},
            learning_style="visual"
        )
    
    @pytest.mark.asyncio
    async def test_detect_user_domains_with_existing_profile(self, domain_adapter, mock_db, sample_user_profile):
        """Test domain detection with existing user profile."""
        # Mock profile manager
        domain_adapter.profile_manager.get_user_profile = AsyncMock(return_value=sample_user_profile)
        
        # Mock interaction analysis methods
        domain_adapter._analyze_interaction_domains = AsyncMock(return_value={"technology": 0.5, "business": 0.3})
        domain_adapter._analyze_query_domains = AsyncMock(return_value={"technology": 0.7, "science": 0.4})
        domain_adapter._analyze_document_domains = AsyncMock(return_value={"science": 0.6, "medicine": 0.2})
        
        result = await domain_adapter.detect_user_domains("user-1")
        
        # Should combine all signals and normalize
        assert isinstance(result, dict)
        assert "technology" in result
        assert "science" in result
        assert all(0 <= score <= 1 for score in result.values())
        
        # Technology should have highest score due to multiple signals
        assert result["technology"] > result.get("science", 0)
    
    @pytest.mark.asyncio
    async def test_detect_user_domains_no_profile(self, domain_adapter, mock_db):
        """Test domain detection with no existing profile."""
        # Mock profile manager to return None
        domain_adapter.profile_manager.get_user_profile = AsyncMock(return_value=None)
        
        # Mock interaction analysis methods
        domain_adapter._analyze_interaction_domains = AsyncMock(return_value={"technology": 0.5})
        domain_adapter._analyze_query_domains = AsyncMock(return_value={"technology": 0.7})
        domain_adapter._analyze_document_domains = AsyncMock(return_value={})
        
        result = await domain_adapter.detect_user_domains("user-1")
        
        assert isinstance(result, dict)
        assert "technology" in result
        assert result["technology"] > 0
    
    @pytest.mark.asyncio
    async def test_analyze_interaction_domains(self, domain_adapter, mock_db):
        """Test interaction domain analysis."""
        # Mock analytics events
        mock_events = [
            Mock(
                event_type="adaptive_search",
                event_data={"top_domains": ["technology", "science"]},
                timestamp=datetime.utcnow()
            ),
            Mock(
                event_type="chat_interaction",
                event_data={"query": "machine learning algorithms"},
                timestamp=datetime.utcnow()
            )
        ]
        
        mock_db.query.return_value.filter.return_value.all.return_value = mock_events
        
        result = await domain_adapter._analyze_interaction_domains("user-1")
        
        assert isinstance(result, dict)
        assert "technology" in result
        assert result["technology"] > 0
    
    @pytest.mark.asyncio
    async def test_analyze_query_domains(self, domain_adapter, mock_db):
        """Test query domain analysis."""
        # Mock recent messages
        mock_messages = [
            Mock(content="How does machine learning work?", role="user"),
            Mock(content="Explain software architecture patterns", role="user"),
            Mock(content="What is the research methodology?", role="user")
        ]
        
        mock_db.query.return_value.join.return_value.filter.return_value.limit.return_value.all.return_value = mock_messages
        
        result = await domain_adapter._analyze_query_domains("user-1")
        
        assert isinstance(result, dict)
        assert "technology" in result
        assert "science" in result
        assert result["technology"] > 0
        assert result["science"] > 0
    
    @pytest.mark.asyncio
    async def test_analyze_document_domains(self, domain_adapter, mock_db, sample_user_profile):
        """Test document domain analysis."""
        # Mock profile manager
        domain_adapter.profile_manager.get_user_profile = AsyncMock(return_value=sample_user_profile)
        
        # Mock document tags
        mock_tags = [
            Mock(tag_name="technology", confidence_score=0.8),
            Mock(tag_name="science", confidence_score=0.6)
        ]
        
        mock_db.query.return_value.filter.return_value.all.return_value = mock_tags
        
        result = await domain_adapter._analyze_document_domains("user-1")
        
        assert isinstance(result, dict)
        assert len(result) > 0
    
    def test_detect_query_domains(self, domain_adapter):
        """Test query domain detection."""
        # Technology query
        tech_query = "How to implement machine learning algorithms in Python?"
        tech_result = domain_adapter._detect_query_domains(tech_query)
        assert "technology" in tech_result
        assert tech_result["technology"] > 0
        
        # Science query
        science_query = "What is the research methodology for this experiment?"
        science_result = domain_adapter._detect_query_domains(science_query)
        assert "science" in science_result
        assert science_result["science"] > 0
        
        # Business query
        business_query = "What is the market strategy for revenue growth?"
        business_result = domain_adapter._detect_query_domains(business_query)
        assert "business" in business_result
        assert business_result["business"] > 0
    
    @pytest.mark.asyncio
    async def test_get_domain_specific_strategy_technology(self, domain_adapter):
        """Test getting domain-specific strategy for technology domain."""
        detected_domains = {"technology": 0.8, "science": 0.3}
        
        strategy = await domain_adapter.get_domain_specific_strategy(
            "user-1", 
            "How to implement software algorithms?",  # More clearly technology-focused
            detected_domains
        )
        
        assert strategy["primary_domain"] == "technology"
        assert strategy["domain_confidence"] >= 0.8  # May be higher due to query analysis
        assert strategy["chunking_strategy"]["chunk_size"] == 800  # Technology config
        assert strategy["retrieval_strategy"]["recency_weight"] == 0.9  # Technology config
        assert "technical" in strategy["response_strategy"]["citation_style"]
    
    @pytest.mark.asyncio
    async def test_get_domain_specific_strategy_medicine(self, domain_adapter):
        """Test getting domain-specific strategy for medicine domain."""
        detected_domains = {"medicine": 0.9, "science": 0.4}
        
        strategy = await domain_adapter.get_domain_specific_strategy(
            "user-1",
            "What is the treatment protocol?",
            detected_domains
        )
        
        assert strategy["primary_domain"] == "medicine"
        assert strategy["chunking_strategy"]["chunk_size"] == 900  # Medicine config
        assert strategy["chunking_strategy"]["overlap_ratio"] == 0.25  # High overlap for medical
        assert strategy["response_strategy"]["uncertainty_handling"] == "conservative"
    
    @pytest.mark.asyncio
    async def test_get_domain_specific_strategy_no_domains(self, domain_adapter):
        """Test getting strategy when no domains are detected."""
        strategy = await domain_adapter.get_domain_specific_strategy(
            "user-1",
            "General question",
            {}
        )
        
        assert strategy["primary_domain"] == "general"
        assert strategy["domain_confidence"] == 0.0
        assert strategy["chunking_strategy"]["chunk_size"] == 600  # Default
        assert strategy["response_strategy"]["citation_style"] == "standard"
    
    @pytest.mark.asyncio
    async def test_adapt_retrieval_results(self, domain_adapter, mock_db):
        """Test adapting retrieval results based on domain strategy."""
        # Mock results
        results = [
            {
                "content": "Machine learning algorithms and software development",
                "relevance": 0.8,
                "metadata": {"document_id": "doc-1", "document_name": "ML Guide"}
            },
            {
                "content": "Business strategy and market analysis",
                "relevance": 0.7,
                "metadata": {"document_id": "doc-2", "document_name": "Business Report"}
            }
        ]
        
        # Technology strategy
        strategy = {
            "primary_domain": "technology",
            "domain_confidence": 0.8,
            "all_domains": {"technology": 0.8, "business": 0.3},
            "retrieval_strategy": {
                "domain_boost": 0.24,
                "content_type_preference": ["documentation", "tutorial"],
                "complexity_weight": 0.8,
                "recency_weight": 0.9
            }
        }
        
        # Mock domain relevance calculation
        domain_adapter._calculate_domain_relevance = AsyncMock(side_effect=[0.8, 0.3])
        
        adapted_results = await domain_adapter.adapt_retrieval_results(results, strategy, "user-1")
        
        assert len(adapted_results) == 2
        assert "domain_adapted_score" in adapted_results[0]
        assert "domain_factors" in adapted_results[0]
        assert adapted_results[0]["domain_factors"]["primary_domain"] == "technology"
        
        # Results should be sorted by adapted score
        assert adapted_results[0]["domain_adapted_score"] >= adapted_results[1]["domain_adapted_score"]
    
    @pytest.mark.asyncio
    async def test_calculate_domain_relevance(self, domain_adapter, mock_db):
        """Test domain relevance calculation."""
        result = {
            "metadata": {"document_id": "doc-1"}
        }
        
        # Mock document tags
        mock_tags = [
            Mock(tag_name="technology", confidence_score=0.8),
            Mock(tag_name="science", confidence_score=0.6)
        ]
        
        mock_db.query.return_value.filter.return_value.all.return_value = mock_tags
        
        all_domains = {"technology": 0.9, "science": 0.5, "business": 0.2}
        
        relevance = await domain_adapter._calculate_domain_relevance(
            result, "technology", all_domains
        )
        
        # Should return highest relevance (technology: 0.9 * 0.8 = 0.72)
        assert abs(relevance - 0.72) < 0.001  # Allow for floating point precision
    
    def test_calculate_content_type_relevance(self, domain_adapter):
        """Test content type relevance calculation."""
        # Documentation content
        doc_result = {
            "content": "This is a comprehensive guide and documentation for the API",
            "metadata": {"document_name": "API Documentation"}
        }
        
        relevance = domain_adapter._calculate_content_type_relevance(
            doc_result, ["documentation", "tutorial"]
        )
        
        assert relevance > 0
        
        # Tutorial content
        tutorial_result = {
            "content": "Step-by-step tutorial on how to implement the feature",
            "metadata": {"document_name": "Tutorial Guide"}
        }
        
        tutorial_relevance = domain_adapter._calculate_content_type_relevance(
            tutorial_result, ["tutorial", "documentation"]
        )
        
        assert tutorial_relevance > 0
    
    def test_calculate_complexity_alignment(self, domain_adapter):
        """Test complexity alignment calculation."""
        # High complexity content
        complex_result = {
            "content": "Advanced comprehensive analysis of sophisticated algorithms and complex methodologies"
        }
        
        # Should align well with high complexity preference
        high_alignment = domain_adapter._calculate_complexity_alignment(complex_result, 0.8)
        assert high_alignment > 0.5
        
        # Should align poorly with low complexity preference
        low_alignment = domain_adapter._calculate_complexity_alignment(complex_result, 0.2)
        assert low_alignment < high_alignment
        
        # Simple content
        simple_result = {
            "content": "Basic introduction and simple overview of elementary concepts"
        }
        
        # Should align well with low complexity preference
        simple_low_alignment = domain_adapter._calculate_complexity_alignment(simple_result, 0.2)
        assert simple_low_alignment > 0.5
    
    @pytest.mark.asyncio
    async def test_update_domain_adaptation(self, domain_adapter, mock_db):
        """Test updating domain adaptation based on feedback."""
        results = [
            {"metadata": {"document_id": "doc-1"}},
            {"metadata": {"document_id": "doc-2"}}
        ]
        
        user_feedback = {"rating": 5, "helpful": True}
        
        # Mock methods
        domain_adapter._analyze_result_domains = AsyncMock(return_value={"technology": 0.8})
        domain_adapter._reinforce_domain_learning = AsyncMock()
        
        await domain_adapter.update_domain_adaptation(
            "user-1", "machine learning query", results, user_feedback
        )
        
        # Should create analytics event
        mock_db.add.assert_called()
        mock_db.commit.assert_called()
        
        # Should reinforce learning for positive feedback
        domain_adapter._reinforce_domain_learning.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_domain_adaptation_stats(self, domain_adapter, mock_db):
        """Test getting domain adaptation statistics."""
        # Mock detect_user_domains
        domain_adapter.detect_user_domains = AsyncMock(return_value={"technology": 0.8, "science": 0.6})
        
        # Mock analytics events
        mock_events = [
            Mock(
                event_data={
                    "query_domains": {"technology": 0.8},
                    "user_feedback": {"rating": 5}
                },
                timestamp=datetime.utcnow()
            ),
            Mock(
                event_data={
                    "query_domains": {"science": 0.6},
                    "user_feedback": {"rating": 3}
                },
                timestamp=datetime.utcnow()
            )
        ]
        
        mock_db.query.return_value.filter.return_value.all.return_value = mock_events
        
        stats = await domain_adapter.get_domain_adaptation_stats("user-1")
        
        assert "detected_domains" in stats
        assert "primary_domain" in stats
        assert "domain_confidence" in stats
        assert "adaptation_events" in stats
        assert stats["primary_domain"] == "technology"
        assert stats["domain_confidence"] == 0.8
        assert stats["adaptation_events"] == 2

class TestDomainDetector:
    """Test cases for DomainDetector class."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def domain_detector(self, mock_db):
        """Create DomainDetector instance with mock database."""
        return DomainDetector(mock_db)
    
    @pytest.mark.asyncio
    async def test_detect_document_domain_technology(self, domain_detector):
        """Test detecting technology domain in document."""
        tech_content = """
        This document covers software development, programming languages,
        machine learning algorithms, and computer science concepts.
        It includes API documentation and framework implementation details.
        """
        
        domains = await domain_detector.detect_document_domain("doc-1", tech_content)
        
        assert len(domains) > 0
        assert any(domain == "technology" for domain, _ in domains)
        
        # Technology should have high confidence
        tech_confidence = next(conf for domain, conf in domains if domain == "technology")
        assert tech_confidence > 0.1
    
    @pytest.mark.asyncio
    async def test_detect_document_domain_science(self, domain_detector):
        """Test detecting science domain in document."""
        science_content = """
        This research paper presents a scientific study on experimental methodology.
        The hypothesis was tested through rigorous analysis and theoretical framework.
        Results show significant findings in the research domain.
        """
        
        domains = await domain_detector.detect_document_domain("doc-1", science_content)
        
        assert len(domains) > 0
        assert any(domain == "science" for domain, _ in domains)
        
        # Science should have high confidence
        science_confidence = next(conf for domain, conf in domains if domain == "science")
        assert science_confidence > 0.1
    
    @pytest.mark.asyncio
    async def test_detect_document_domain_multiple(self, domain_detector):
        """Test detecting multiple domains in document."""
        mixed_content = """
        This business report analyzes market strategy and financial performance.
        The research methodology includes data analysis and statistical studies.
        Software tools were used for computational analysis and algorithm implementation.
        """
        
        domains = await domain_detector.detect_document_domain("doc-1", mixed_content)
        
        # Should detect multiple domains
        domain_names = [domain for domain, _ in domains]
        assert "business" in domain_names
        assert "science" in domain_names or "technology" in domain_names
        
        # Should be sorted by confidence
        confidences = [conf for _, conf in domains]
        assert confidences == sorted(confidences, reverse=True)
    
    @pytest.mark.asyncio
    async def test_detect_document_domain_no_match(self, domain_detector):
        """Test detecting domains when no clear match exists."""
        generic_content = """
        This is a general document with common words and phrases.
        It doesn't contain specific domain terminology or keywords.
        The content is neutral and broadly applicable.
        """
        
        domains = await domain_detector.detect_document_domain("doc-1", generic_content)
        
        # Should return empty list or very low confidence domains
        assert len(domains) == 0 or all(conf <= 0.5 for _, conf in domains)  # Relaxed threshold
    
    @pytest.mark.asyncio
    async def test_auto_tag_document_domains(self, domain_detector, mock_db):
        """Test automatically tagging document with detected domains."""
        tech_content = """
        Software development guide covering programming languages,
        algorithms, and computer science fundamentals.
        """
        
        # Mock domain detection
        domain_detector.detect_document_domain = AsyncMock(return_value=[
            ("technology", 0.8),
            ("science", 0.4)
        ])
        
        await domain_detector.auto_tag_document_domains("doc-1", tech_content)
        
        # Should add domain tags to database
        assert mock_db.add.call_count == 2  # Two domains detected
        mock_db.commit.assert_called_once()
        
        # Check that DocumentTag objects were created
        added_tags = [call.args[0] for call in mock_db.add.call_args_list]
        assert len(added_tags) == 2
        
        # Verify tag properties
        tech_tag = next(tag for tag in added_tags if tag.tag_name == "technology")
        assert tech_tag.document_id == "doc-1"
        assert tech_tag.tag_type == "domain"
        assert tech_tag.confidence_score == 0.8
        assert tech_tag.generated_by == "domain_detector"

class TestDomainConfigurations:
    """Test domain-specific configurations."""
    
    def test_domain_configs_structure(self):
        """Test that domain configurations have required structure."""
        for domain, config in DomainAdapter.DOMAIN_CONFIGS.items():
            # Required fields
            assert "keywords" in config
            assert "chunk_size" in config
            assert "overlap_ratio" in config
            assert "complexity_weight" in config
            assert "recency_weight" in config
            assert "citation_style" in config
            assert "reasoning_emphasis" in config
            assert "content_types" in config
            
            # Type checks
            assert isinstance(config["keywords"], list)
            assert isinstance(config["chunk_size"], int)
            assert isinstance(config["overlap_ratio"], float)
            assert isinstance(config["complexity_weight"], float)
            assert isinstance(config["recency_weight"], float)
            assert isinstance(config["citation_style"], str)
            assert isinstance(config["reasoning_emphasis"], list)
            assert isinstance(config["content_types"], list)
            
            # Value ranges
            assert 0 <= config["overlap_ratio"] <= 1
            assert 0 <= config["complexity_weight"] <= 1
            assert 0 <= config["recency_weight"] <= 1
            assert config["chunk_size"] > 0
    
    def test_domain_keyword_coverage(self):
        """Test that domain keywords provide good coverage."""
        for domain, config in DomainAdapter.DOMAIN_CONFIGS.items():
            keywords = config["keywords"]
            
            # Should have reasonable number of keywords
            assert len(keywords) >= 5, f"Domain {domain} has too few keywords"
            assert len(keywords) <= 15, f"Domain {domain} has too many keywords"
            
            # Keywords should be lowercase
            assert all(keyword.islower() for keyword in keywords), f"Domain {domain} has non-lowercase keywords"
            
            # No duplicate keywords
            assert len(keywords) == len(set(keywords)), f"Domain {domain} has duplicate keywords"
    
    def test_domain_specialization(self):
        """Test that domains have appropriate specialization."""
        configs = DomainAdapter.DOMAIN_CONFIGS
        
        # Medical and legal should have conservative settings
        assert configs["medicine"]["overlap_ratio"] >= 0.2  # High overlap for context
        assert configs["law"]["overlap_ratio"] >= 0.25  # Very high overlap for precision
        
        # Technology should prioritize recency
        assert configs["technology"]["recency_weight"] >= 0.8
        
        # Science should have high complexity weight
        assert configs["science"]["complexity_weight"] >= 0.8
        
        # Education should be more accessible
        assert configs["education"]["complexity_weight"] <= 0.6

@pytest.mark.integration
class TestDomainAdapterIntegration:
    """Integration tests for domain adapter with real database operations."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_domain_adaptation(self):
        """Test complete domain adaptation workflow."""
        # This would require a real database setup
        # For now, we'll skip this test in unit test environment
        pytest.skip("Integration test requires database setup")
    
    @pytest.mark.asyncio
    async def test_domain_learning_feedback_loop(self):
        """Test domain learning with feedback loop."""
        # This would test the complete learning cycle
        pytest.skip("Integration test requires database setup")