"""
Tests for Zotero Research Integration Service

Tests the integration between Zotero references and research/note-taking features.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session

from ..services.zotero.zotero_research_integration_service import ZoteroResearchIntegrationService
from ..models.zotero_models import ZoteroItem


class TestZoteroResearchIntegrationService:
    """Test suite for ZoteroResearchIntegrationService"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.service = ZoteroResearchIntegrationService()
        self.mock_db = Mock(spec=Session)
        self.user_id = "test-user-123"
        
        # Sample Zotero item
        self.sample_item = ZoteroItem(
            id="item-123",
            user_id=self.user_id,
            zotero_item_key="ABC123",
            item_type="article",
            title="Machine Learning in Healthcare",
            creators=[
                {"firstName": "John", "lastName": "Smith", "creatorType": "author"},
                {"firstName": "Jane", "lastName": "Doe", "creatorType": "author"}
            ],
            publication_title="Journal of Medical AI",
            date="2023-05-15",
            abstract_note="This paper explores machine learning applications in healthcare."
        )
    
    def test_extract_reference_links(self):
        """Test extraction of reference links from content"""
        content = """
        This note discusses [[ref:item-123]] and mentions @[Machine Learning Paper].
        Also references [[ref:item-456]] for comparison.
        """
        
        links = self.service.extract_reference_links(content)
        
        assert len(links['itemIds']) == 2
        assert "item-123" in links['itemIds']
        assert "item-456" in links['itemIds']
        assert len(links['mentions']) == 1
        assert "Machine Learning Paper" in links['mentions']
    
    def test_extract_reference_links_no_links(self):
        """Test extraction when no links are present"""
        content = "This is a regular note without any reference links."
        
        links = self.service.extract_reference_links(content)
        
        assert len(links['itemIds']) == 0
        assert len(links['mentions']) == 0
    
    def test_convert_item_to_reference(self):
        """Test conversion of Zotero item to reference format"""
        reference = self.service._convert_item_to_reference(self.sample_item)
        
        assert reference['id'] == "item-123"
        assert reference['title'] == "Machine Learning in Healthcare"
        assert reference['creators'] == ["John Smith", "Jane Doe"]
        assert reference['year'] == 2023
        assert reference['publicationTitle'] == "Journal of Medical AI"
        assert reference['relevance'] == 1.0
        assert reference['citationKey'] == "Smith2023"
        assert reference['abstractNote'] == "This paper explores machine learning applications in healthcare."
    
    @pytest.mark.asyncio
    async def test_process_note_content_with_item_ids(self):
        """Test processing note content with item ID references"""
        content = "This discusses [[ref:item-123]] in detail."
        
        # Mock database query
        self.mock_db.query.return_value.filter.return_value.first.return_value = self.sample_item
        
        result = await self.service.process_note_content(
            content, self.user_id, self.mock_db
        )
        
        assert "Machine Learning in Healthcare" in result['processedContent']
        assert "[Machine Learning in Healthcare](zotero:item-123)" in result['processedContent']
        assert len(result['references']) == 1
        assert result['references'][0]['title'] == "Machine Learning in Healthcare"
        assert result['originalLinks']['itemIds'] == ["item-123"]
    
    @pytest.mark.asyncio
    async def test_process_note_content_with_mentions(self):
        """Test processing note content with reference mentions"""
        content = "This paper @[Machine Learning] is interesting."
        
        # Mock search service
        with patch.object(self.service.search_service, 'search_items') as mock_search:
            mock_search.return_value = {
                'items': [self.sample_item]
            }
            
            result = await self.service.process_note_content(
                content, self.user_id, self.mock_db
            )
            
            assert "Machine Learning in Healthcare" in result['processedContent']
            assert len(result['references']) == 1
            assert result['originalLinks']['mentions'] == ["Machine Learning"]
    
    @pytest.mark.asyncio
    async def test_create_research_summary_with_reference_ids(self):
        """Test creating research summary with specific reference IDs"""
        topic = "Machine Learning in Healthcare"
        reference_ids = ["item-123"]
        
        # Mock database query
        self.mock_db.query.return_value.filter.return_value.first.return_value = self.sample_item
        
        result = await self.service.create_research_summary(
            topic, self.user_id, self.mock_db, reference_ids
        )
        
        assert result['topic'] == topic
        assert "Research Summary: Machine Learning in Healthcare" in result['summary']
        assert len(result['references']) == 1
        assert len(result['keyFindings']) > 0
        assert len(result['gaps']) > 0
        assert len(result['recommendations']) > 0
    
    @pytest.mark.asyncio
    async def test_create_research_summary_with_search(self):
        """Test creating research summary by searching for references"""
        topic = "AI in Medicine"
        
        # Mock search service
        with patch.object(self.service.search_service, 'search_items') as mock_search:
            mock_search.return_value = {
                'items': [self.sample_item]
            }
            
            result = await self.service.create_research_summary(
                topic, self.user_id, self.mock_db
            )
            
            assert result['topic'] == topic
            assert len(result['references']) == 1
            assert "AI in Medicine" in result['summary']
    
    def test_generate_summary_content(self):
        """Test generation of summary content"""
        topic = "Test Topic"
        references = [
            {
                'title': 'Paper 1',
                'creators': ['Author A', 'Author B'],
                'year': 2023,
                'publicationTitle': 'Journal A'
            },
            {
                'title': 'Paper 2',
                'creators': ['Author C'],
                'year': 2022,
                'publicationTitle': 'Journal B'
            }
        ]
        
        summary = self.service._generate_summary_content(topic, references)
        
        assert "Research Summary: Test Topic" in summary
        assert "based on 2 references" in summary
        assert "Paper 1" in summary
        assert "Author A, Author B (2023)" in summary
        assert "Journal A" in summary
    
    def test_extract_key_findings(self):
        """Test extraction of key findings"""
        references = [
            {'year': 2023, 'title': 'Recent Paper'},
            {'year': 2022, 'title': 'Another Paper'},
            {'year': 2021, 'title': 'Older Paper'}
        ]
        
        findings = self.service._extract_key_findings(references)
        
        assert len(findings) > 0
        assert "Analysis of 3 papers" in findings[0]
        assert any("recent research activity" in finding for finding in findings)
    
    def test_identify_research_gaps(self):
        """Test identification of research gaps"""
        topic = "Test Topic"
        references = [
            {'year': 2020, 'publicationTitle': 'Journal A'},
            {'year': 2019, 'publicationTitle': 'Journal A'},
            {'year': 2018, 'publicationTitle': 'Journal B'}
        ]
        
        gaps = self.service._identify_research_gaps(topic, references)
        
        assert len(gaps) > 0
        assert any("recent studies" in gap for gap in gaps)
        assert any("diversity" in gap for gap in gaps)
    
    def test_generate_recommendations(self):
        """Test generation of recommendations"""
        topic = "Test Topic"
        references = [{'title': f'Paper {i}'} for i in range(15)]  # Many references
        gaps = ["Gap 1", "Gap 2"]
        
        recommendations = self.service._generate_recommendations(topic, references, gaps)
        
        assert len(recommendations) > 0
        assert any("systematic literature review" in rec for rec in recommendations)
        assert any("meta-analysis" in rec for rec in recommendations)
        assert any("research gaps" in rec for rec in recommendations)
    
    @pytest.mark.asyncio
    async def test_get_research_context(self):
        """Test getting research context"""
        topic = "Machine Learning"
        
        # Mock search service
        with patch.object(self.service.search_service, 'search_items') as mock_search:
            mock_search.return_value = {
                'items': [self.sample_item]
            }
            
            result = await self.service.get_research_context(
                topic, self.user_id, self.mock_db
            )
            
            assert result['topic'] == topic
            assert len(result['relevantReferences']) == 1
            assert len(result['suggestedQuestions']) > 0
            assert len(result['researchGaps']) > 0
    
    def test_generate_suggested_questions(self):
        """Test generation of suggested questions"""
        topic = "AI Ethics"
        references = [{'title': f'Paper {i}'} for i in range(8)]  # Many references
        
        questions = self.service._generate_suggested_questions(topic, references)
        
        assert len(questions) > 0
        assert any("current trends" in q for q in questions)
        assert any("methodologies" in q for q in questions)
        assert any("consensus" in q for q in questions)  # Should appear with many refs
    
    @pytest.mark.asyncio
    async def test_create_research_assistance_prompt(self):
        """Test creation of research assistance prompt"""
        question = "What are the benefits of machine learning in healthcare?"
        reference_ids = ["item-123"]
        
        # Mock database query
        self.mock_db.query.return_value.filter.return_value.first.return_value = self.sample_item
        
        prompt = await self.service.create_research_assistance_prompt(
            question, self.user_id, self.mock_db, reference_ids
        )
        
        assert question in prompt
        assert "Context from your Zotero library:" in prompt
        assert "Machine Learning in Healthcare" in prompt
        assert "John Smith, Jane Doe" in prompt
        assert "comprehensive answer" in prompt
    
    @pytest.mark.asyncio
    async def test_suggest_related_references(self):
        """Test suggesting related references"""
        note_content = "This note discusses machine learning applications in medical diagnosis."
        existing_ids = ["item-456"]
        
        # Mock search service
        with patch.object(self.service.search_service, 'search_items') as mock_search:
            mock_search.return_value = {
                'items': [self.sample_item]
            }
            
            suggestions = await self.service.suggest_related_references(
                note_content, self.user_id, self.mock_db, existing_ids
            )
            
            assert len(suggestions) > 0
            assert suggestions[0]['title'] == "Machine Learning in Healthcare"
            assert suggestions[0]['id'] not in existing_ids
    
    def test_extract_key_terms(self):
        """Test extraction of key terms"""
        content = "Machine learning algorithms are used in healthcare applications for medical diagnosis and treatment."
        
        key_terms = self.service._extract_key_terms(content)
        
        assert len(key_terms) > 0
        assert "machine" in key_terms
        assert "learning" in key_terms
        assert "healthcare" in key_terms
    
    @pytest.mark.asyncio
    async def test_export_research_project(self):
        """Test exporting research project"""
        project_data = {
            'title': 'Test Project',
            'description': 'A test research project',
            'status': 'active',
            'references': [
                {
                    'title': 'Test Paper',
                    'creators': ['Author A'],
                    'year': 2023,
                    'publicationTitle': 'Test Journal'
                }
            ],
            'notes': [
                {
                    'title': 'Test Note',
                    'content': 'This is a test note with [[ref:item-123]].',
                    'tags': ['test', 'research']
                }
            ]
        }
        
        # Mock database query for note processing
        self.mock_db.query.return_value.filter.return_value.first.return_value = self.sample_item
        
        export_content = await self.service.export_research_project(
            project_data, self.user_id, self.mock_db
        )
        
        assert "# Test Project" in export_content
        assert "A test research project" in export_content
        assert "## References" in export_content
        assert "Author A (2023). Test Paper" in export_content
        assert "## Research Notes" in export_content
        assert "### Test Note" in export_content
        assert "**Tags:** test, research" in export_content


class TestZoteroResearchIntegrationEdgeCases:
    """Test edge cases and error handling"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.service = ZoteroResearchIntegrationService()
        self.mock_db = Mock(spec=Session)
        self.user_id = "test-user-123"
    
    def test_extract_links_malformed(self):
        """Test extraction with malformed link syntax"""
        content = "This has [[ref:unclosed and @[incomplete mention"
        
        links = self.service.extract_reference_links(content)
        
        assert len(links['itemIds']) == 0
        assert len(links['mentions']) == 0
    
    def test_convert_item_no_creators(self):
        """Test conversion with item that has no creators"""
        item = ZoteroItem(
            id="item-123",
            title="Anonymous Paper",
            creators=[],
            date="2023"
        )
        
        reference = self.service._convert_item_to_reference(item)
        
        assert reference['creators'] == []
        assert reference['citationKey'] == "Unknown2023"
    
    def test_convert_item_no_date(self):
        """Test conversion with item that has no date"""
        item = ZoteroItem(
            id="item-123",
            title="Undated Paper",
            creators=[{"firstName": "John", "lastName": "Smith"}],
            date=None
        )
        
        reference = self.service._convert_item_to_reference(item)
        
        assert reference['year'] is None
        assert "Smith" in reference['citationKey']
    
    @pytest.mark.asyncio
    async def test_process_note_missing_item(self):
        """Test processing note with missing item reference"""
        content = "This references [[ref:nonexistent-item]]."
        
        # Mock database query returning None
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = await self.service.process_note_content(
            content, self.user_id, self.mock_db
        )
        
        # Should not crash, should return original content
        assert "[[ref:nonexistent-item]]" in result['processedContent']
        assert len(result['references']) == 0
    
    @pytest.mark.asyncio
    async def test_suggest_references_no_results(self):
        """Test suggesting references when no results found"""
        note_content = "This note has very unique terminology that won't match anything."
        
        # Mock search service returning no results
        with patch.object(self.service.search_service, 'search_items') as mock_search:
            mock_search.return_value = {'items': []}
            
            suggestions = await self.service.suggest_related_references(
                note_content, self.user_id, self.mock_db
            )
            
            assert len(suggestions) == 0
    
    def test_generate_summary_no_references(self):
        """Test generating summary with no references"""
        topic = "Empty Topic"
        references = []
        
        summary = self.service._generate_summary_content(topic, references)
        
        assert "No references found for topic: Empty Topic" in summary
    
    def test_extract_key_terms_empty_content(self):
        """Test extracting key terms from empty content"""
        content = ""
        
        key_terms = self.service._extract_key_terms(content)
        
        assert len(key_terms) == 0
    
    def test_extract_key_terms_short_words(self):
        """Test extracting key terms with only short words"""
        content = "a an the is it to of in on at by for"
        
        key_terms = self.service._extract_key_terms(content)
        
        assert len(key_terms) == 0  # All words are too short