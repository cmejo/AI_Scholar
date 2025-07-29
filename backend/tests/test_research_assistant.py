"""
Tests for Research Assistant Service
"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from sqlalchemy.orm import Session
from services.research_assistant import (
    ResearchAssistant, ResearchType, ResearchDomain,
    LiteratureReviewSection, ResearchProposal,
    MethodologyRecommendation, DataAnalysisGuidance
)
from core.database import Document, DocumentChunk

@pytest.fixture
def mock_db():
    """Mock database session"""
    return Mock(spec=Session)

@pytest.fixture
def research_assistant(mock_db):
    """Create ResearchAssistant instance with mocked dependencies"""
    with patch('services.research_assistant.MultiModalProcessor'), \
         patch('services.research_assistant.TopicModelingService'), \
         patch('services.research_assistant.KnowledgeGraphService'):
        
        assistant = ResearchAssistant(mock_db)
        return assistant

@pytest.fixture
def sample_documents():
    """Sample documents for testing"""
    return [
        Document(
            id="doc1",
            user_id="user1",
            name="Machine Learning Research",
            content_type="application/pdf",
            size=1024,
            status="completed",
            created_at=datetime.utcnow()
        ),
        Document(
            id="doc2",
            user_id="user1",
            name="Deep Learning Applications",
            content_type="application/pdf",
            size=2048,
            status="completed",
            created_at=datetime.utcnow()
        )
    ]

@pytest.fixture
def sample_chunks():
    """Sample document chunks for testing"""
    return [
        DocumentChunk(
            id="chunk1",
            document_id="doc1",
            content="The study found that machine learning algorithms significantly improved prediction accuracy. Results show a 25% improvement over traditional methods.",
            chunk_index=0
        ),
        DocumentChunk(
            id="chunk2",
            document_id="doc1",
            content="Further research is needed to explore the limitations of current approaches. The gap in understanding deep learning interpretability remains a challenge.",
            chunk_index=1
        ),
        DocumentChunk(
            id="chunk3",
            document_id="doc2",
            content="The experimental design used a randomized controlled trial with 1000 participants. Statistical analysis revealed significant correlations.",
            chunk_index=0
        )
    ]

class TestResearchAssistant:
    """Test cases for ResearchAssistant"""

    def test_initialization(self, mock_db):
        """Test research assistant initialization"""
        with patch('services.research_assistant.MultiModalProcessor'), \
             patch('services.research_assistant.TopicModelingService'), \
             patch('services.research_assistant.KnowledgeGraphService'):
            
            assistant = ResearchAssistant(mock_db)
            assert assistant.db == mock_db
            assert hasattr(assistant, 'research_templates')
            assert hasattr(assistant, 'methodology_database')
            assert hasattr(assistant, 'analysis_patterns')

    def test_load_research_templates(self, research_assistant):
        """Test loading of research templates"""
        templates = research_assistant.research_templates
        
        assert "literature_review" in templates
        assert "research_proposal" in templates
        
        # Check literature review template structure
        lit_review = templates["literature_review"]
        assert "sections" in lit_review
        assert "structure" in lit_review
        assert len(lit_review["sections"]) > 0
        
        # Check research proposal template structure
        proposal = templates["research_proposal"]
        assert "sections" in proposal
        assert "word_limits" in proposal

    def test_load_methodology_database(self, research_assistant):
        """Test loading of methodology database"""
        method_db = research_assistant.methodology_database
        
        assert ResearchType.QUANTITATIVE in method_db
        assert ResearchType.QUALITATIVE in method_db
        assert ResearchType.MIXED_METHODS in method_db
        
        # Check quantitative methods
        quant_methods = method_db[ResearchType.QUANTITATIVE]
        assert "methods" in quant_methods
        assert "analysis_types" in quant_methods
        assert "software" in quant_methods
        assert len(quant_methods["methods"]) > 0

    def test_load_analysis_patterns(self, research_assistant):
        """Test loading of analysis patterns"""
        patterns = research_assistant.analysis_patterns
        
        assert "statistical_tests" in patterns
        assert "sample_size" in patterns
        
        # Check statistical tests structure
        stats = patterns["statistical_tests"]
        assert "comparison" in stats
        assert "relationship" in stats
        assert "prediction" in stats

    @pytest.mark.asyncio
    async def test_get_relevant_documents(self, research_assistant, mock_db, sample_documents):
        """Test getting relevant documents"""
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value.filter.return_value.limit.return_value.all.return_value = sample_documents
        mock_db.query.return_value = mock_query
        
        documents = await research_assistant._get_relevant_documents(
            topic="machine learning",
            user_id="user1",
            limit=10
        )
        
        assert len(documents) == 2
        assert documents[0].name == "Machine Learning Research"

    @pytest.mark.asyncio
    async def test_get_relevant_documents_with_ids(self, research_assistant, mock_db, sample_documents):
        """Test getting relevant documents with specific IDs"""
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.limit.return_value.all.return_value = sample_documents[:1]
        mock_db.query.return_value = mock_query
        
        documents = await research_assistant._get_relevant_documents(
            topic="machine learning",
            user_id="user1",
            document_ids=["doc1"]
        )
        
        assert len(documents) == 1
        assert documents[0].id == "doc1"

    @pytest.mark.asyncio
    async def test_extract_research_themes(self, research_assistant, sample_documents):
        """Test extracting research themes"""
        # Mock topic service
        mock_topic_result = Mock()
        mock_topic_result.topics = [
            Mock(
                name="Machine Learning",
                keywords=["machine", "learning", "algorithm"],
                weight=0.8,
                description="ML research",
                document_count=2
            )
        ]
        
        research_assistant.topic_service.analyze_document_topics = Mock(return_value=mock_topic_result)
        
        themes = await research_assistant._extract_research_themes(sample_documents)
        
        assert len(themes) == 1
        assert themes[0]["name"] == "Machine Learning"
        assert themes[0]["weight"] == 0.8

    @pytest.mark.asyncio
    async def test_extract_key_findings(self, research_assistant, mock_db, sample_documents, sample_chunks):
        """Test extracting key findings from documents"""
        # Mock database query for chunks
        mock_db.query.return_value.filter.return_value.all.return_value = sample_chunks[:2]
        
        findings = await research_assistant._extract_key_findings(sample_documents[:1])
        
        assert len(findings) > 0
        # Should find the sentence with "found that"
        assert any("found that" in finding["text"] for finding in findings)

    @pytest.mark.asyncio
    async def test_identify_methodologies(self, research_assistant, mock_db, sample_documents, sample_chunks):
        """Test identifying research methodologies"""
        # Mock database query for chunks
        mock_db.query.return_value.filter.return_value.all.return_value = sample_chunks
        
        methodologies = await research_assistant._identify_methodologies(sample_documents)
        
        assert len(methodologies) > 0
        # Should identify experimental methodology from the chunks
        method_types = [m["methodology"] for m in methodologies]
        assert "experiment" in method_types or "statistical" in method_types

    @pytest.mark.asyncio
    async def test_identify_research_gaps(self, research_assistant, mock_db, sample_documents, sample_chunks):
        """Test identifying research gaps"""
        # Mock database query for chunks
        mock_db.query.return_value.filter.return_value.all.return_value = sample_chunks
        
        themes = [
            {"name": "Machine Learning", "document_count": 1},
            {"name": "Deep Learning", "document_count": 1}
        ]
        
        gaps = await research_assistant._identify_research_gaps(sample_documents, themes)
        
        assert len(gaps) > 0
        # Should find the gap mentioned in sample_chunks
        assert any("further research" in gap["description"].lower() for gap in gaps)

    @pytest.mark.asyncio
    async def test_generate_introduction_section(self, research_assistant):
        """Test generating introduction section"""
        themes = [
            {"name": "Machine Learning", "weight": 0.8},
            {"name": "Deep Learning", "weight": 0.6}
        ]
        
        section = await research_assistant._generate_introduction_section(
            topic="AI Research",
            themes=themes,
            doc_count=5
        )
        
        assert isinstance(section, LiteratureReviewSection)
        assert section.title == "Introduction"
        assert "AI Research" in section.content
        assert "5 relevant documents" in section.content
        assert section.section_type == "introduction"

    @pytest.mark.asyncio
    async def test_track_research_event(self, research_assistant, mock_db):
        """Test tracking research analytics events"""
        await research_assistant._track_research_event(
            user_id="user1",
            event_type="test_event",
            event_data={"test": "data"}
        )
        
        # Verify database operations
        assert mock_db.add.called
        assert mock_db.commit.called

    def test_research_type_enum(self):
        """Test ResearchType enum values"""
        assert ResearchType.QUANTITATIVE == "quantitative"
        assert ResearchType.QUALITATIVE == "qualitative"
        assert ResearchType.MIXED_METHODS == "mixed_methods"
        assert ResearchType.EXPERIMENTAL == "experimental"

    def test_research_domain_enum(self):
        """Test ResearchDomain enum values"""
        assert ResearchDomain.COMPUTER_SCIENCE == "computer_science"
        assert ResearchDomain.ENGINEERING == "engineering"
        assert ResearchDomain.MEDICINE == "medicine"
        assert ResearchDomain.PSYCHOLOGY == "psychology"

    def test_literature_review_section_dataclass(self):
        """Test LiteratureReviewSection dataclass"""
        section = LiteratureReviewSection(
            title="Test Section",
            content="Test content",
            citations=["Citation 1", "Citation 2"],
            key_findings=["Finding 1"],
            gaps_identified=["Gap 1"],
            section_type="test"
        )
        
        assert section.title == "Test Section"
        assert len(section.citations) == 2
        assert len(section.key_findings) == 1

    def test_research_proposal_dataclass(self):
        """Test ResearchProposal dataclass"""
        proposal = ResearchProposal(
            title="Test Proposal",
            abstract="Test abstract",
            introduction="Test introduction",
            literature_review="Test review",
            methodology="Test methodology",
            expected_outcomes="Test outcomes",
            timeline={"month1": "Task 1"},
            budget_estimate="$10000",
            references=["Ref 1"],
            research_questions=["Question 1"],
            hypotheses=["Hypothesis 1"]
        )
        
        assert proposal.title == "Test Proposal"
        assert len(proposal.research_questions) == 1
        assert len(proposal.hypotheses) == 1

    def test_methodology_recommendation_dataclass(self):
        """Test MethodologyRecommendation dataclass"""
        recommendation = MethodologyRecommendation(
            method_name="Survey Research",
            description="A method for collecting data",
            advantages=["Cost effective", "Large sample"],
            disadvantages=["Response bias"],
            applicability_score=0.8,
            required_resources=["Survey platform"],
            estimated_duration="3 months",
            complexity_level="intermediate",
            references=["Reference 1"]
        )
        
        assert recommendation.method_name == "Survey Research"
        assert recommendation.applicability_score == 0.8
        assert len(recommendation.advantages) == 2

    def test_data_analysis_guidance_dataclass(self):
        """Test DataAnalysisGuidance dataclass"""
        guidance = DataAnalysisGuidance(
            analysis_type="descriptive",
            statistical_methods=["Mean", "Standard deviation"],
            software_recommendations=["R", "Python"],
            step_by_step_guide=["Step 1", "Step 2"],
            interpretation_guidelines="Guidelines text",
            common_pitfalls=["Pitfall 1"],
            validation_methods=["Cross-validation"],
            reporting_standards=["APA style"]
        )
        
        assert guidance.analysis_type == "descriptive"
        assert len(guidance.statistical_methods) == 2
        assert len(guidance.software_recommendations) == 2

if __name__ == "__main__":
    pytest.main([__file__])