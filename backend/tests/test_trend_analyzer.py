"""
Tests for the TrendAnalyzer service
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from services.trend_analyzer import TrendAnalyzer
from core.database import Document, DocumentTag, AnalyticsEvent
from models.schemas import TagType

class TestTrendAnalyzer:
    """Test cases for TrendAnalyzer service"""
    
    @pytest.fixture
    def trend_analyzer(self):
        """Create TrendAnalyzer instance"""
        return TrendAnalyzer()
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def sample_documents(self):
        """Create sample documents for testing"""
        base_time = datetime.now() - timedelta(days=15)
        
        return [
            Mock(
                id="doc1",
                user_id="user1",
                name="AI Research Paper",
                size=50000,
                content_type="application/pdf",
                created_at=base_time
            ),
            Mock(
                id="doc2",
                user_id="user1",
                name="Machine Learning Tutorial",
                size=30000,
                content_type="application/pdf",
                created_at=base_time + timedelta(days=5)
            ),
            Mock(
                id="doc3",
                user_id="user1",
                name="Deep Learning Guide",
                size=75000,
                content_type="application/pdf",
                created_at=base_time + timedelta(days=10)
            ),
            Mock(
                id="doc4",
                user_id="user1",
                name="Neural Networks Basics",
                size=40000,
                content_type="application/pdf",
                created_at=base_time + timedelta(days=12)
            )
        ]
    
    @pytest.fixture
    def sample_tags(self):
        """Create sample tags for testing"""
        return [
            # Topic tags
            Mock(id="tag1", document_id="doc1", tag_name="artificial_intelligence", 
                 tag_type="topic", confidence_score=0.9, created_at=datetime.now()),
            Mock(id="tag2", document_id="doc1", tag_name="machine_learning", 
                 tag_type="topic", confidence_score=0.85, created_at=datetime.now()),
            Mock(id="tag3", document_id="doc2", tag_name="machine_learning", 
                 tag_type="topic", confidence_score=0.8, created_at=datetime.now()),
            Mock(id="tag4", document_id="doc2", tag_name="tutorial", 
                 tag_type="topic", confidence_score=0.75, created_at=datetime.now()),
            Mock(id="tag5", document_id="doc3", tag_name="deep_learning", 
                 tag_type="topic", confidence_score=0.9, created_at=datetime.now()),
            Mock(id="tag6", document_id="doc4", tag_name="neural_networks", 
                 tag_type="topic", confidence_score=0.85, created_at=datetime.now()),
            
            # Domain tags
            Mock(id="tag7", document_id="doc1", tag_name="computer_science", 
                 tag_type="domain", confidence_score=0.9, created_at=datetime.now()),
            Mock(id="tag8", document_id="doc2", tag_name="computer_science", 
                 tag_type="domain", confidence_score=0.85, created_at=datetime.now()),
            Mock(id="tag9", document_id="doc3", tag_name="computer_science", 
                 tag_type="domain", confidence_score=0.9, created_at=datetime.now()),
            Mock(id="tag10", document_id="doc4", tag_name="computer_science", 
                 tag_type="domain", confidence_score=0.8, created_at=datetime.now()),
            
            # Complexity tags
            Mock(id="tag11", document_id="doc1", tag_name="complexity_advanced", 
                 tag_type="complexity", confidence_score=0.8, created_at=datetime.now()),
            Mock(id="tag12", document_id="doc2", tag_name="complexity_intermediate", 
                 tag_type="complexity", confidence_score=0.85, created_at=datetime.now()),
            Mock(id="tag13", document_id="doc3", tag_name="complexity_advanced", 
                 tag_type="complexity", confidence_score=0.9, created_at=datetime.now()),
            Mock(id="tag14", document_id="doc4", tag_name="complexity_beginner", 
                 tag_type="complexity", confidence_score=0.75, created_at=datetime.now()),
        ]
    
    @pytest.mark.asyncio
    async def test_analyze_document_collection_trends_success(
        self, trend_analyzer, mock_db, sample_documents, sample_tags
    ):
        """Test successful document collection trend analysis"""
        # Mock database queries
        mock_db.query.return_value.filter.return_value.all.return_value = sample_documents
        
        # Mock tag queries
        def mock_tag_query(*args):
            mock_query = Mock()
            mock_query.filter.return_value.all.return_value = sample_tags
            return mock_query
        
        mock_db.query.side_effect = [
            Mock(filter=Mock(return_value=Mock(all=Mock(return_value=sample_documents)))),
            mock_tag_query(),
            mock_tag_query(),
            mock_tag_query(),
            mock_tag_query(),
            mock_tag_query()
        ]
        
        # Test trend analysis
        result = await trend_analyzer.analyze_document_collection_trends(
            user_id="user1",
            db=mock_db,
            time_range_days=30
        )
        
        # Verify results
        assert result["status"] == "success"
        assert result["document_count"] == 4
        assert "trends" in result
        assert "insights" in result
        assert "analysis_period" in result
        
        # Check trend categories
        trends = result["trends"]
        assert "tag_trends" in trends
        assert "temporal_trends" in trends
        assert "topic_evolution" in trends
        assert "complexity_trends" in trends
        assert "domain_trends" in trends
    
    @pytest.mark.asyncio
    async def test_analyze_document_collection_trends_insufficient_data(
        self, trend_analyzer, mock_db
    ):
        """Test trend analysis with insufficient data"""
        # Mock insufficient documents
        mock_db.query.return_value.filter.return_value.all.return_value = [Mock(), Mock()]  # Only 2 docs
        
        result = await trend_analyzer.analyze_document_collection_trends(
            user_id="user1",
            db=mock_db,
            time_range_days=30
        )
        
        assert result["status"] == "insufficient_data"
        assert result["document_count"] == 2
        assert "Need at least" in result["message"]
    
    @pytest.mark.asyncio
    async def test_analyze_tag_trends(self, trend_analyzer, sample_documents, sample_tags, mock_db):
        """Test tag trend analysis"""
        # Mock tag query
        mock_db.query.return_value.filter.return_value.all.return_value = sample_tags
        
        result = await trend_analyzer._analyze_tag_trends(sample_documents, mock_db)
        
        # Verify tag trend structure
        assert "topic" in result
        assert "domain" in result
        assert "complexity" in result
        
        # Check topic trends
        topic_trends = result["topic"]
        assert "total_tags" in topic_trends
        assert "unique_tags" in topic_trends
        assert "trending_tags" in topic_trends
        assert "tag_distribution" in topic_trends
        
        # Verify trending tags have required fields
        if topic_trends["trending_tags"]:
            trending_tag = topic_trends["trending_tags"][0]
            assert "tag_name" in trending_tag
            assert "frequency" in trending_tag
            assert "average_confidence" in trending_tag
            assert "trend_strength" in trending_tag
    
    @pytest.mark.asyncio
    async def test_analyze_temporal_trends(self, trend_analyzer, sample_documents, mock_db):
        """Test temporal trend analysis"""
        result = await trend_analyzer._analyze_temporal_trends(sample_documents, mock_db)
        
        # Verify temporal trend structure
        assert "daily_distribution" in result
        assert "weekly_distribution" in result
        assert "monthly_distribution" in result
        assert "statistics" in result
        assert "patterns" in result
        
        # Check statistics
        stats = result["statistics"]
        assert "average_daily_uploads" in stats
        assert "total_days_active" in stats
        
        # Verify distributions are not empty
        assert len(result["daily_distribution"]) > 0
        assert len(result["weekly_distribution"]) > 0
    
    @pytest.mark.asyncio
    async def test_analyze_topic_evolution(self, trend_analyzer, sample_documents, sample_tags, mock_db):
        """Test topic evolution analysis"""
        # Mock topic tags with timestamps
        topic_tags = [
            (tag, doc.created_at) for tag in sample_tags 
            if tag.tag_type == "topic"
            for doc in sample_documents 
            if doc.id == tag.document_id
        ]
        
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = topic_tags
        
        result = await trend_analyzer._analyze_topic_evolution(sample_documents, mock_db)
        
        # Verify topic evolution structure
        if result.get("status") != "no_topic_data":
            assert "topic_evolution" in result
            assert "timeline" in result
            assert "emerging_topics" in result
            assert "declining_topics" in result
            assert "total_topics_tracked" in result
    
    @pytest.mark.asyncio
    async def test_analyze_complexity_trends(self, trend_analyzer, sample_documents, sample_tags, mock_db):
        """Test complexity trend analysis"""
        # Mock complexity tags with timestamps
        complexity_tags = [
            (tag, doc.created_at) for tag in sample_tags 
            if tag.tag_type == "complexity"
            for doc in sample_documents 
            if doc.id == tag.document_id
        ]
        
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = complexity_tags
        
        result = await trend_analyzer._analyze_complexity_trends(sample_documents, mock_db)
        
        # Verify complexity trend structure
        if result.get("status") != "no_complexity_data":
            assert "trend_analysis" in result
            assert "complexity_distribution" in result
            assert "timeline" in result
            assert "total_documents_analyzed" in result
    
    @pytest.mark.asyncio
    async def test_analyze_domain_trends(self, trend_analyzer, sample_documents, sample_tags, mock_db):
        """Test domain trend analysis"""
        # Mock domain tags with timestamps
        domain_tags = [
            (tag, doc.created_at) for tag in sample_tags 
            if tag.tag_type == "domain"
            for doc in sample_documents 
            if doc.id == tag.document_id
        ]
        
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = domain_tags
        
        result = await trend_analyzer._analyze_domain_trends(sample_documents, mock_db)
        
        # Verify domain trend structure
        if result.get("status") != "no_domain_data":
            assert "domain_statistics" in result
            assert "dominant_domains" in result
            assert "domain_timeline" in result
            assert "domain_shifts" in result
            assert "total_unique_domains" in result
    
    @pytest.mark.asyncio
    async def test_compare_documents_success(self, trend_analyzer, sample_documents, sample_tags, mock_db):
        """Test successful document comparison"""
        # Set up the documents with correct IDs
        sample_documents[0].id = "doc1"
        sample_documents[1].id = "doc2"
        
        # Mock document query
        mock_db.query.return_value.filter.return_value.all.return_value = sample_documents[:2]
        
        # Mock tag queries for comparison - need to handle multiple calls
        def mock_query_side_effect(*args):
            mock_query = Mock()
            mock_query.filter.return_value.all.return_value = sample_tags
            return mock_query
        
        mock_db.query.side_effect = [
            Mock(filter=Mock(return_value=Mock(all=Mock(return_value=sample_documents[:2])))),  # Document query
            mock_query_side_effect(),  # Tag comparison query
            mock_query_side_effect(),  # Complexity comparison query
            mock_query_side_effect(),  # Domain comparison query
            mock_query_side_effect(),  # Topic comparison query
        ]
        
        result = await trend_analyzer.compare_documents(
            document_ids=["doc1", "doc2"],
            db=mock_db
        )
        
        # Verify comparison structure
        assert "documents" in result
        assert "comparisons" in result
        assert "overall_similarity" in result
        assert "insights" in result
        
        # Check document info
        assert len(result["documents"]) == 2
        
        # Check comparison types
        comparisons = result["comparisons"]
        assert "tag_comparison" in comparisons
        assert "complexity_comparison" in comparisons
        assert "domain_comparison" in comparisons
        assert "topic_comparison" in comparisons
        assert "metadata_comparison" in comparisons
    
    @pytest.mark.asyncio
    async def test_compare_documents_insufficient_documents(self, trend_analyzer, mock_db):
        """Test document comparison with insufficient documents"""
        with pytest.raises(ValueError, match="Need at least 2 documents"):
            await trend_analyzer.compare_documents(
                document_ids=["doc1"],
                db=mock_db
            )
    
    @pytest.mark.asyncio
    async def test_compare_documents_missing_documents(self, trend_analyzer, mock_db):
        """Test document comparison with missing documents"""
        # Mock only one document found
        mock_db.query.return_value.filter.return_value.all.return_value = [Mock(id="doc1")]
        
        with pytest.raises(ValueError, match="Documents not found"):
            await trend_analyzer.compare_documents(
                document_ids=["doc1", "doc2"],
                db=mock_db
            )
    
    @pytest.mark.asyncio
    async def test_compare_document_tags(self, trend_analyzer, sample_documents, sample_tags, mock_db):
        """Test document tag comparison"""
        # Mock tag query
        mock_db.query.return_value.filter.return_value.all.return_value = sample_tags
        
        result = await trend_analyzer._compare_document_tags(sample_documents[:2], mock_db)
        
        # Verify tag comparison structure
        comparison_key = f"{sample_documents[0].name}_vs_{sample_documents[1].name}"
        assert comparison_key in result
        
        # Check tag type comparisons
        tag_comparison = result[comparison_key]
        for tag_type in ["topic", "domain", "complexity"]:
            if tag_type in tag_comparison:
                type_comp = tag_comparison[tag_type]
                assert "overlap_score" in type_comp
                assert "common_tags" in type_comp
                assert "unique_to_doc1" in type_comp
                assert "unique_to_doc2" in type_comp
    
    @pytest.mark.asyncio
    async def test_compare_document_complexity(self, trend_analyzer, sample_documents, sample_tags, mock_db):
        """Test document complexity comparison"""
        # Filter complexity tags
        complexity_tags = [tag for tag in sample_tags if tag.tag_type == "complexity"]
        mock_db.query.return_value.filter.return_value.all.return_value = complexity_tags
        
        result = await trend_analyzer._compare_document_complexity(sample_documents[:2], mock_db)
        
        # Verify complexity comparison structure
        assert "document_complexities" in result
        assert "pairwise_comparisons" in result
        
        # Check document complexities
        doc_complexities = result["document_complexities"]
        for doc in sample_documents[:2]:
            assert doc.id in doc_complexities
            complexity = doc_complexities[doc.id]
            assert "level" in complexity
            assert "level_name" in complexity
            assert "confidence" in complexity
        
        # Check pairwise comparisons
        pairwise = result["pairwise_comparisons"]
        comparison_key = f"{sample_documents[0].name}_vs_{sample_documents[1].name}"
        if comparison_key in pairwise:
            comparison = pairwise[comparison_key]
            assert "doc1_complexity" in comparison
            assert "doc2_complexity" in comparison
            assert "level_difference" in comparison
            assert "similarity_score" in comparison
            assert "comparison" in comparison
    
    @pytest.mark.asyncio
    async def test_compare_document_domains(self, trend_analyzer, sample_documents, sample_tags, mock_db):
        """Test document domain comparison"""
        # Filter domain tags
        domain_tags = [tag for tag in sample_tags if tag.tag_type == "domain"]
        mock_db.query.return_value.filter.return_value.all.return_value = domain_tags
        
        result = await trend_analyzer._compare_document_domains(sample_documents[:2], mock_db)
        
        # Verify domain comparison structure
        assert "document_domains" in result
        assert "pairwise_comparisons" in result
        
        # Check pairwise comparisons
        pairwise = result["pairwise_comparisons"]
        comparison_key = f"{sample_documents[0].name}_vs_{sample_documents[1].name}"
        if comparison_key in pairwise:
            comparison = pairwise[comparison_key]
            assert "overlap_score" in comparison
            assert "common_domains" in comparison
            assert "doc1_unique_domains" in comparison
            assert "doc2_unique_domains" in comparison
            assert "relationship" in comparison
    
    @pytest.mark.asyncio
    async def test_compare_document_topics(self, trend_analyzer, sample_documents, sample_tags, mock_db):
        """Test document topic comparison"""
        # Filter topic tags
        topic_tags = [tag for tag in sample_tags if tag.tag_type == "topic"]
        mock_db.query.return_value.filter.return_value.all.return_value = topic_tags
        
        result = await trend_analyzer._compare_document_topics(sample_documents[:2], mock_db)
        
        # Verify topic comparison structure
        assert "document_topics" in result
        assert "pairwise_comparisons" in result
        
        # Check pairwise comparisons
        pairwise = result["pairwise_comparisons"]
        comparison_key = f"{sample_documents[0].name}_vs_{sample_documents[1].name}"
        if comparison_key in pairwise:
            comparison = pairwise[comparison_key]
            assert "overlap_score" in comparison
            assert "weighted_similarity" in comparison
            assert "common_topics" in comparison
            assert "doc1_unique_topics" in comparison
            assert "doc2_unique_topics" in comparison
            assert "relationship" in comparison
    
    @pytest.mark.asyncio
    async def test_compare_document_metadata(self, trend_analyzer, sample_documents):
        """Test document metadata comparison"""
        result = await trend_analyzer._compare_document_metadata(sample_documents[:2])
        
        # Verify metadata comparison structure
        comparison_key = f"{sample_documents[0].name}_vs_{sample_documents[1].name}"
        assert comparison_key in result
        
        comparison = result[comparison_key]
        assert "size_similarity" in comparison
        assert "size_difference_bytes" in comparison
        assert "time_difference_days" in comparison
        assert "same_content_type" in comparison
        assert "doc1_metadata" in comparison
        assert "doc2_metadata" in comparison
    
    @pytest.mark.asyncio
    async def test_calculate_overall_similarity(self, trend_analyzer):
        """Test overall similarity calculation"""
        # Mock comparison data
        comparisons = {
            "tag_comparison": {
                "doc1_vs_doc2": {
                    "topic": {"overlap_score": 0.8},
                    "domain": {"overlap_score": 0.9}
                }
            },
            "complexity_comparison": {
                "pairwise_comparisons": {
                    "doc1_vs_doc2": {"similarity_score": 0.7}
                }
            },
            "domain_comparison": {
                "pairwise_comparisons": {
                    "doc1_vs_doc2": {"overlap_score": 0.6}
                }
            },
            "topic_comparison": {
                "pairwise_comparisons": {
                    "doc1_vs_doc2": {"weighted_similarity": 0.75}
                }
            }
        }
        
        result = await trend_analyzer._calculate_overall_similarity(comparisons)
        
        # Verify similarity calculation
        assert "doc1_vs_doc2" in result
        similarity = result["doc1_vs_doc2"]
        assert 0 <= similarity <= 1
    
    @pytest.mark.asyncio
    async def test_generate_trend_insights(self, trend_analyzer):
        """Test trend insight generation"""
        # Mock trend data
        tag_trends = {
            "topic": {
                "trending_tags": [
                    {"tag_name": "ai", "average_confidence": 0.9}
                ]
            }
        }
        
        temporal_trends = {
            "patterns": [
                {
                    "type": "increasing_activity",
                    "description": "Activity increased",
                    "confidence": 0.8
                }
            ]
        }
        
        topic_evolution = {
            "emerging_topics": ["machine_learning", "deep_learning"],
            "declining_topics": ["old_topic"]
        }
        
        complexity_trends = {
            "trend_analysis": {
                "complexity_trend": "increasing",
                "trend_strength": 0.7
            }
        }
        
        domain_trends = {
            "domain_shifts": [
                {
                    "type": "new_domains_emerged",
                    "description": "New domains appeared"
                }
            ]
        }
        
        result = await trend_analyzer._generate_trend_insights(
            tag_trends, temporal_trends, topic_evolution, 
            complexity_trends, domain_trends
        )
        
        # Verify insights structure
        assert isinstance(result, list)
        
        # Check insight fields
        for insight in result:
            assert "type" in insight
            assert "category" in insight
            assert "insight" in insight
            assert "confidence" in insight
            assert "recommendation" in insight
    
    @pytest.mark.asyncio
    async def test_generate_comparison_insights(self, trend_analyzer, sample_documents):
        """Test comparison insight generation"""
        # Mock comparison data
        comparisons = {
            "tag_comparison": {
                "doc1_vs_doc2": {
                    "topic": {
                        "overlap_score": 0.8,
                        "common_tags": ["ai", "ml"]
                    }
                }
            },
            "complexity_comparison": {
                "pairwise_comparisons": {
                    "doc1_vs_doc2": {
                        "comparison": "different",
                        "doc1_complexity": {"level_name": "advanced"},
                        "doc2_complexity": {"level_name": "beginner"}
                    }
                }
            }
        }
        
        result = await trend_analyzer._generate_comparison_insights(comparisons, sample_documents[:2])
        
        # Verify insights structure
        assert isinstance(result, list)
        
        # Check insight fields
        for insight in result:
            assert "type" in insight
            assert "category" in insight
            assert "insight" in insight
            assert "documents" in insight
    
    def test_trend_analyzer_initialization(self, trend_analyzer):
        """Test TrendAnalyzer initialization"""
        assert trend_analyzer.min_documents_for_trend == 3
        assert trend_analyzer.trend_confidence_threshold == 0.7
        assert trend_analyzer.comparison_similarity_threshold == 0.6
    
    @pytest.mark.asyncio
    async def test_error_handling_in_trend_analysis(self, trend_analyzer, mock_db):
        """Test error handling in trend analysis"""
        # Mock database error
        mock_db.query.side_effect = Exception("Database error")
        
        with pytest.raises(Exception, match="Database error"):
            await trend_analyzer.analyze_document_collection_trends(
                user_id="user1",
                db=mock_db
            )
    
    @pytest.mark.asyncio
    async def test_error_handling_in_document_comparison(self, trend_analyzer, mock_db):
        """Test error handling in document comparison"""
        # Mock database error
        mock_db.query.side_effect = Exception("Database error")
        
        with pytest.raises(Exception, match="Database error"):
            await trend_analyzer.compare_documents(
                document_ids=["doc1", "doc2"],
                db=mock_db
            )

if __name__ == "__main__":
    pytest.main([__file__])