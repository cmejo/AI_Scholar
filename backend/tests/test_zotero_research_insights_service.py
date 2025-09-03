"""
Tests for Zotero Research Insights Service
"""
import json
import pytest
import numpy as np
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from collections import Counter
from sqlalchemy.orm import Session

from services.zotero.zotero_research_insights_service import ZoteroResearchInsightsService
from models.zotero_models import ZoteroItem, ZoteroLibrary, ZoteroConnection


class TestZoteroResearchInsightsService:
    """Test cases for Zotero Research Insights Service"""
    
    @pytest.fixture
    def insights_service(self):
        """Create research insights service instance"""
        return ZoteroResearchInsightsService()
    
    @pytest.fixture
    def mock_zotero_items(self):
        """Create mock Zotero items for testing"""
        items = []
        
        # Create items with different topics and years
        topics_data = [
            {
                "title": "Machine Learning in Healthcare",
                "year": 2023,
                "topics": ["machine learning", "healthcare", "AI"],
                "methodology": "experimental"
            },
            {
                "title": "Deep Learning for Image Recognition",
                "year": 2022,
                "topics": ["deep learning", "computer vision", "AI"],
                "methodology": "experimental"
            },
            {
                "title": "Natural Language Processing Applications",
                "year": 2023,
                "topics": ["NLP", "language models", "AI"],
                "methodology": "survey"
            },
            {
                "title": "Blockchain Technology in Finance",
                "year": 2021,
                "topics": ["blockchain", "finance", "cryptocurrency"],
                "methodology": "case study"
            },
            {
                "title": "Quantum Computing Algorithms",
                "year": 2022,
                "topics": ["quantum computing", "algorithms", "physics"],
                "methodology": "theoretical"
            }
        ]
        
        for i, data in enumerate(topics_data):
            item = ZoteroItem(
                id=f"item_{i}",
                library_id="lib_123",
                zotero_item_key=f"KEY{i}",
                item_type="journalArticle",
                title=data["title"],
                publication_year=data["year"],
                abstract_note=f"Abstract for {data['title']}",
                creators=[{"firstName": "Author", "lastName": f"Name{i}", "creatorType": "author"}],
                tags=data["topics"],
                item_metadata={
                    "ai_analysis": {
                        "results": {
                            "topics": {
                                "primary_topics": data["topics"],
                                "methodology": data["methodology"],
                                "research_domain": "Computer Science"
                            }
                        }
                    }
                }
            )
            items.append(item)
        
        return items
    
    @pytest.mark.asyncio
    async def test_analyze_research_landscape_success(self, insights_service, mock_zotero_items):
        """Test successful research landscape analysis"""
        user_id = "user_123"
        
        with patch.object(insights_service, '_get_user_items_for_analysis', return_value=mock_zotero_items):
            result = await insights_service.analyze_research_landscape(
                user_id=user_id,
                library_id=None,
                analysis_types=["topics", "trends", "gaps", "networks"]
            )
            
            # Verify result structure
            assert result["user_id"] == user_id
            assert result["total_items"] == len(mock_zotero_items)
            assert "results" in result
            assert "topics" in result["results"]
            assert "trends" in result["results"]
            assert "gaps" in result["results"]
            assert "networks" in result["results"]
            assert "analysis_timestamp" in result
    
    @pytest.mark.asyncio
    async def test_analyze_research_landscape_insufficient_items(self, insights_service):
        """Test research landscape analysis with insufficient items"""
        user_id = "user_123"
        
        # Mock insufficient items
        few_items = [Mock() for _ in range(3)]
        
        with patch.object(insights_service, '_get_user_items_for_analysis', return_value=few_items):
            result = await insights_service.analyze_research_landscape(
                user_id=user_id,
                analysis_types=["topics"]
            )
            
            assert "error" in result
            assert "Insufficient items" in result["error"]
            assert result["item_count"] == 3
    
    @pytest.mark.asyncio
    async def test_identify_research_themes_success(self, insights_service, mock_zotero_items):
        """Test successful research theme identification"""
        user_id = "user_123"
        
        with patch.object(insights_service, '_get_user_items_for_analysis', return_value=mock_zotero_items), \
             patch.object(insights_service, '_cluster_research_themes') as mock_cluster, \
             patch.object(insights_service, '_generate_theme_insights', return_value=["Insight 1"]), \
             patch.object(insights_service, '_suggest_research_directions', return_value=["Direction 1"]):
            
            # Mock clustering results
            mock_themes = [
                {
                    "theme_id": "theme_0",
                    "theme_name": "AI and Machine Learning",
                    "keywords": ["machine learning", "AI", "deep learning"],
                    "summary": "Research focused on AI applications",
                    "item_count": 3,
                    "items": [],
                    "coherence_score": 0.8
                }
            ]
            mock_cluster.return_value = mock_themes
            
            result = await insights_service.identify_research_themes(
                user_id=user_id,
                clustering_method="kmeans",
                num_themes=3
            )
            
            # Verify result structure
            assert result["user_id"] == user_id
            assert result["clustering_method"] == "kmeans"
            assert result["num_themes"] == 1
            assert "themes" in result
            assert len(result["themes"]) == 1
            
            # Verify theme structure
            theme = result["themes"][0]
            assert theme["theme_name"] == "AI and Machine Learning"
            assert "insights" in theme
            assert "research_directions" in theme
    
    @pytest.mark.asyncio
    async def test_identify_research_themes_insufficient_items(self, insights_service):
        """Test theme identification with insufficient items"""
        user_id = "user_123"
        
        # Mock insufficient items
        few_items = [Mock() for _ in range(2)]
        
        with patch.object(insights_service, '_get_user_items_for_analysis', return_value=few_items):
            result = await insights_service.identify_research_themes(
                user_id=user_id,
                clustering_method="kmeans"
            )
            
            assert "error" in result
            assert "Insufficient items" in result["error"]
    
    @pytest.mark.asyncio
    async def test_detect_research_gaps_success(self, insights_service, mock_zotero_items):
        """Test successful research gap detection"""
        user_id = "user_123"
        
        with patch.object(insights_service, '_get_user_items_for_analysis', return_value=mock_zotero_items), \
             patch.object(insights_service, '_detect_temporal_gaps', return_value={"temporal_gaps": []}), \
             patch.object(insights_service, '_detect_topical_gaps', return_value={"topical_gaps": []}), \
             patch.object(insights_service, '_detect_methodological_gaps', return_value={"methodological_gaps": []}), \
             patch.object(insights_service, '_generate_gap_filling_recommendations', return_value=[]):
            
            result = await insights_service.detect_research_gaps(
                user_id=user_id,
                gap_types=["temporal", "topical", "methodological"]
            )
            
            # Verify result structure
            assert result["user_id"] == user_id
            assert result["gap_types"] == ["temporal", "topical", "methodological"]
            assert result["total_items"] == len(mock_zotero_items)
            assert "gaps_detected" in result
            assert "recommendations" in result
            assert "analysis_timestamp" in result
    
    @pytest.mark.asyncio
    async def test_detect_research_gaps_limited_items(self, insights_service):
        """Test gap detection with limited items"""
        user_id = "user_123"
        
        # Mock limited items
        limited_items = [Mock() for _ in range(5)]
        
        with patch.object(insights_service, '_get_user_items_for_analysis', return_value=limited_items):
            result = await insights_service.detect_research_gaps(
                user_id=user_id,
                gap_types=["temporal"]
            )
            
            assert "warning" in result
            assert "Limited items" in result["warning"]
            assert result["item_count"] == 5
    
    @pytest.mark.asyncio
    async def test_analyze_research_trends_success(self, insights_service, mock_zotero_items):
        """Test successful research trend analysis"""
        user_id = "user_123"
        
        with patch.object(insights_service, '_get_user_items_for_analysis', return_value=mock_zotero_items), \
             patch.object(insights_service, '_analyze_temporal_trends', return_value={"temporal_trends": []}), \
             patch.object(insights_service, '_analyze_topical_trends', return_value={"topical_trends": []}), \
             patch.object(insights_service, '_analyze_citation_trends', return_value={"citation_trends": []}), \
             patch.object(insights_service, '_analyze_collaboration_trends', return_value={"collaboration_trends": []}), \
             patch.object(insights_service, '_generate_trend_predictions', return_value={"predictions": []}):
            
            result = await insights_service.analyze_research_trends(
                user_id=user_id,
                trend_types=["temporal", "topical", "citation", "collaboration"],
                time_window_years=5
            )
            
            # Verify result structure
            assert result["user_id"] == user_id
            assert result["trend_types"] == ["temporal", "topical", "citation", "collaboration"]
            assert result["time_window_years"] == 5
            assert "trends" in result
            assert "predictions" in result
            assert "analysis_timestamp" in result
    
    @pytest.mark.asyncio
    async def test_analyze_research_trends_insufficient_recent_items(self, insights_service):
        """Test trend analysis with insufficient recent items"""
        user_id = "user_123"
        
        # Mock old items (outside time window)
        old_items = [
            Mock(publication_year=2010),
            Mock(publication_year=2011)
        ]
        
        with patch.object(insights_service, '_get_user_items_for_analysis', return_value=old_items):
            result = await insights_service.analyze_research_trends(
                user_id=user_id,
                time_window_years=5
            )
            
            assert "warning" in result
            assert "Limited recent items" in result["warning"]
    
    @pytest.mark.asyncio
    async def test_analyze_topic_landscape(self, insights_service, mock_zotero_items):
        """Test topic landscape analysis"""
        result = await insights_service._analyze_topic_landscape(mock_zotero_items)
        
        # Verify result structure
        assert "total_topics" in result
        assert "most_common_topics" in result
        assert "topic_distribution" in result
        assert "topic_evolution" in result
        assert "coverage_analysis" in result
        
        # Verify coverage analysis
        coverage = result["coverage_analysis"]
        assert "items_with_topics" in coverage
        assert "coverage_percentage" in coverage
    
    @pytest.mark.asyncio
    async def test_analyze_research_trends_method(self, insights_service, mock_zotero_items):
        """Test research trends analysis method"""
        result = await insights_service._analyze_research_trends(mock_zotero_items)
        
        # Verify result structure
        assert "publication_trends" in result
        assert "topic_trends_by_year" in result
        assert "emerging_topics" in result
        assert "time_span" in result
        assert "total_years" in result
        
        # Verify publication trends
        pub_trends = result["publication_trends"]
        assert "years" in pub_trends
        assert "counts" in pub_trends
        assert "trend_direction" in pub_trends
    
    @pytest.mark.asyncio
    async def test_detect_research_gaps_method(self, insights_service, mock_zotero_items):
        """Test research gaps detection method"""
        result = await insights_service._detect_research_gaps(mock_zotero_items)
        
        # Verify result structure
        assert "temporal_gaps" in result
        assert "underrepresented_topics" in result
        assert "methodology_gaps" in result
        assert "coverage_analysis" in result
        
        # Verify methodology gaps
        method_gaps = result["methodology_gaps"]
        assert "covered_methodologies" in method_gaps
        assert "methodology_distribution" in method_gaps
        assert "suggestions" in method_gaps
    
    @pytest.mark.asyncio
    async def test_analyze_research_networks(self, insights_service, mock_zotero_items):
        """Test research networks analysis"""
        result = await insights_service._analyze_research_networks(mock_zotero_items)
        
        # Verify result structure
        assert "author_network" in result
        assert "topic_network" in result
        assert "citation_patterns" in result
        assert "network_metrics" in result
        
        # Verify network metrics
        metrics = result["network_metrics"]
        assert "total_authors" in metrics
        assert "total_topics" in metrics
        assert "collaboration_density" in metrics
    
    @pytest.mark.asyncio
    async def test_cluster_research_themes(self, insights_service):
        """Test research theme clustering"""
        # Mock content and metadata
        contents = [
            "machine learning artificial intelligence",
            "deep learning neural networks",
            "blockchain cryptocurrency finance",
            "quantum computing algorithms"
        ]
        
        metadata = [
            {"item_id": f"item_{i}", "title": f"Paper {i}"}
            for i in range(len(contents))
        ]
        
        with patch.object(insights_service, '_generate_theme_summary', return_value="Test theme summary"):
            themes = await insights_service._cluster_research_themes(
                contents, metadata, "kmeans", 2
            )
            
            # Verify themes structure
            assert len(themes) <= 2  # Should not exceed requested number
            
            for theme in themes:
                assert "theme_id" in theme
                assert "theme_name" in theme
                assert "keywords" in theme
                assert "summary" in theme
                assert "item_count" in theme
                assert "items" in theme
                assert "coherence_score" in theme
    
    @pytest.mark.asyncio
    async def test_generate_theme_summary(self, insights_service):
        """Test theme summary generation"""
        contents = ["machine learning research", "deep learning applications"]
        keywords = ["machine learning", "deep learning", "AI"]
        
        with patch.object(insights_service, '_call_llm', return_value="AI research theme summary"):
            summary = await insights_service._generate_theme_summary(contents, keywords)
            
            assert isinstance(summary, str)
            assert len(summary) > 0
    
    @pytest.mark.asyncio
    async def test_generate_theme_summary_fallback(self, insights_service):
        """Test theme summary generation with LLM failure"""
        contents = ["machine learning research"]
        keywords = ["machine learning", "AI"]
        
        with patch.object(insights_service, '_call_llm', return_value=""):
            summary = await insights_service._generate_theme_summary(contents, keywords)
            
            # Should fallback to keyword-based summary
            assert "machine learning" in summary
            assert "AI" in summary
    
    def test_extract_clustering_content(self, insights_service, mock_zotero_items):
        """Test content extraction for clustering"""
        item = mock_zotero_items[0]
        content = insights_service._extract_clustering_content(item)
        
        assert item.title in content
        assert item.abstract_note in content
        assert all(tag in content for tag in item.tags)
    
    def test_has_topic_analysis(self, insights_service, mock_zotero_items):
        """Test topic analysis detection"""
        item_with_analysis = mock_zotero_items[0]
        assert insights_service._has_topic_analysis(item_with_analysis) is True
        
        # Test item without analysis
        item_without_analysis = ZoteroItem(
            id="item_no_analysis",
            library_id="lib_123",
            zotero_item_key="KEY_NO",
            item_type="journalArticle",
            title="No Analysis Item",
            item_metadata={}
        )
        assert insights_service._has_topic_analysis(item_without_analysis) is False
    
    def test_calculate_frequency_over_time(self, insights_service):
        """Test frequency calculation over time"""
        years = [2020, 2021, 2021, 2022, 2022, 2022]
        result = insights_service._calculate_frequency_over_time(years)
        
        assert "year_counts" in result
        assert "trend" in result
        assert result["year_counts"][2022] == 3
        assert result["year_counts"][2021] == 2
        assert result["year_counts"][2020] == 1
    
    def test_calculate_trend_direction(self, insights_service):
        """Test trend direction calculation"""
        # Test increasing trend
        increasing_values = [1, 2, 3, 4, 5]
        assert insights_service._calculate_trend_direction(increasing_values) == "increasing"
        
        # Test decreasing trend
        decreasing_values = [5, 4, 3, 2, 1]
        assert insights_service._calculate_trend_direction(decreasing_values) == "decreasing"
        
        # Test stable trend
        stable_values = [3, 3, 3, 3, 3]
        assert insights_service._calculate_trend_direction(stable_values) == "stable"
        
        # Test insufficient data
        insufficient_values = [1]
        assert insights_service._calculate_trend_direction(insufficient_values) == "insufficient_data"
    
    def test_identify_emerging_topics(self, insights_service):
        """Test emerging topics identification"""
        topic_trends = {
            2020: [("AI", 5), ("ML", 3)],
            2021: [("AI", 6), ("ML", 4), ("blockchain", 2)],
            2022: [("AI", 7), ("blockchain", 4), ("quantum", 3)],
            2023: [("blockchain", 5), ("quantum", 4), ("metaverse", 2)]
        }
        years = [2020, 2021, 2022, 2023]
        
        emerging = insights_service._identify_emerging_topics(topic_trends, years)
        
        # "metaverse" should be identified as emerging (appears only in recent years)
        assert "metaverse" in emerging
    
    def test_find_temporal_gaps(self, insights_service):
        """Test temporal gaps detection"""
        years = [2018, 2019, 2023, 2024]  # Gap between 2019 and 2023
        gaps = insights_service._find_temporal_gaps(years)
        
        assert len(gaps) == 1
        gap = gaps[0]
        assert gap["start_year"] == 2019
        assert gap["end_year"] == 2023
        assert gap["gap_size"] == 3
        assert gap["missing_years"] == [2020, 2021, 2022]
    
    def test_suggest_missing_methodologies(self, insights_service):
        """Test missing methodologies suggestion"""
        from collections import Counter
        
        covered_methods = Counter(["experimental", "survey"])
        suggestions = insights_service._suggest_missing_methodologies(covered_methods)
        
        # Should suggest methodologies not in covered_methods
        assert "case study" in suggestions
        assert "meta-analysis" in suggestions
        assert "experimental" not in suggestions  # Already covered
        assert "survey" not in suggestions  # Already covered
    
    def test_build_author_network(self, insights_service, mock_zotero_items):
        """Test author network building"""
        network = insights_service._build_author_network(mock_zotero_items)
        
        assert "nodes" in network
        assert "edges" in network
        assert "total_collaborations" in network
        assert "unique_collaborations" in network
        assert "density" in network
        
        # Verify nodes structure
        if network["nodes"]:
            node = network["nodes"][0]
            assert "id" in node
            assert "label" in node
    
    def test_build_topic_network(self, insights_service, mock_zotero_items):
        """Test topic network building"""
        network = insights_service._build_topic_network(mock_zotero_items)
        
        assert "nodes" in network
        assert "edges" in network
        assert "total_cooccurrences" in network
        assert "significant_connections" in network
        
        # Verify nodes structure
        if network["nodes"]:
            node = network["nodes"][0]
            assert "id" in node
            assert "label" in node
    
    def test_analyze_citation_patterns(self, insights_service, mock_zotero_items):
        """Test citation patterns analysis"""
        patterns = insights_service._analyze_citation_patterns(mock_zotero_items)
        
        assert "top_venues" in patterns
        assert "publication_timeline" in patterns
        assert "venue_diversity" in patterns
        assert "temporal_span" in patterns
    
    def test_calculate_theme_coherence(self, insights_service):
        """Test theme coherence calculation"""
        # Mock TF-IDF matrix
        import numpy as np
        from scipy.sparse import csr_matrix
        
        # Create mock sparse matrix
        data = np.array([0.5, 0.3, 0.2, 0.4])
        indices = np.array([0, 1, 2, 0])
        indptr = np.array([0, 2, 4])
        cluster_tfidf = csr_matrix((data, indices, indptr), shape=(2, 3))
        
        coherence = insights_service._calculate_theme_coherence(cluster_tfidf)
        
        assert isinstance(coherence, float)
        assert 0 <= coherence <= 1
    
    @pytest.mark.asyncio
    async def test_call_llm_success(self, insights_service):
        """Test successful LLM call"""
        prompt = "Test prompt"
        expected_response = "Test response"
        
        mock_response = Mock()
        mock_response.json.return_value = {"response": expected_response}
        mock_response.raise_for_status.return_value = None
        
        with patch('requests.post', return_value=mock_response):
            result = await insights_service._call_llm(prompt)
            
            assert result == expected_response
    
    @pytest.mark.asyncio
    async def test_call_llm_failure(self, insights_service):
        """Test LLM call failure"""
        prompt = "Test prompt"
        
        with patch('requests.post', side_effect=Exception("Connection error")):
            result = await insights_service._call_llm(prompt)
            
            # Should return empty string on failure
            assert result == ""