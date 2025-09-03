"""
Tests for Zotero Chat Integration Service

Tests the integration between Zotero references and chat functionality,
including reference context injection, mention linking, and response processing.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session

from ..services.zotero.zotero_chat_integration_service import ZoteroChatIntegrationService
from ..models.zotero_models import ZoteroItem


class TestZoteroChatIntegrationService:
    """Test suite for ZoteroChatIntegrationService"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.service = ZoteroChatIntegrationService()
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
            abstract_note="This paper explores machine learning applications in healthcare.",
            tags=["machine learning", "healthcare", "AI"]
        )
    
    def test_extract_reference_mentions(self):
        """Test extraction of reference mentions from content"""
        content = "I want to discuss @[Machine Learning in Healthcare] and @[Smith, 2023]"
        
        mentions = self.service.extract_reference_mentions(content)
        
        assert len(mentions) == 2
        assert "Machine Learning in Healthcare" in mentions
        assert "Smith, 2023" in mentions
    
    def test_extract_reference_mentions_no_mentions(self):
        """Test extraction when no mentions are present"""
        content = "This is a regular chat message without any references."
        
        mentions = self.service.extract_reference_mentions(content)
        
        assert len(mentions) == 0
    
    def test_convert_to_chat_references(self):
        """Test conversion of Zotero items to chat reference format"""
        items = [self.sample_item]
        
        references = self.service.convert_to_chat_references(items)
        
        assert len(references) == 1
        ref = references[0]
        assert ref['id'] == "item-123"
        assert ref['title'] == "Machine Learning in Healthcare"
        assert ref['creators'] == ["John Smith", "Jane Doe"]
        assert ref['year'] == 2023
        assert ref['publicationTitle'] == "Journal of Medical AI"
        assert ref['citationKey'] == "Smith2023"
        assert ref['relevance'] == 0.8
    
    def test_generate_citation_key(self):
        """Test citation key generation"""
        creators = ["John Smith", "Jane Doe"]
        year = 2023
        
        citation_key = self.service._generate_citation_key(
            self.sample_item, creators, year
        )
        
        assert citation_key == "Smith2023"
    
    def test_generate_citation_key_no_creators(self):
        """Test citation key generation with no creators"""
        creators = []
        year = 2023
        
        citation_key = self.service._generate_citation_key(
            self.sample_item, creators, year
        )
        
        assert citation_key == "Unknown2023"
    
    @pytest.mark.asyncio
    async def test_find_referenced_items(self):
        """Test finding referenced items by mentions"""
        mentions = ["Machine Learning", "Healthcare AI"]
        
        # Mock search service
        with patch.object(self.service.search_service, 'search_items') as mock_search:
            mock_search.return_value = {
                'items': [self.sample_item],
                'total_count': 1
            }
            
            items = await self.service.find_referenced_items(
                mentions, self.user_id, self.mock_db
            )
            
            assert len(items) == 2  # One item per mention
            assert items[0] == self.sample_item
            assert mock_search.call_count == 2
    
    @pytest.mark.asyncio
    async def test_inject_reference_context_with_mentions(self):
        """Test injecting reference context with mentions"""
        content = "Tell me about @[Machine Learning in Healthcare]"
        options = {'includeZoteroContext': True, 'contextType': 'research'}
        
        with patch.object(self.service, 'find_referenced_items') as mock_find:
            mock_find.return_value = [self.sample_item]
            
            enhanced_content, references = await self.service.inject_reference_context(
                content, self.user_id, self.mock_db, options
            )
            
            assert len(references) == 1
            assert references[0]['title'] == "Machine Learning in Healthcare"
            assert "[REFERENCE_CONTEXT]" in enhanced_content
            assert "Research context from referenced papers:" in enhanced_content
    
    @pytest.mark.asyncio
    async def test_inject_reference_context_with_reference_ids(self):
        """Test injecting reference context with specific reference IDs"""
        content = "Analyze these papers"
        options = {
            'includeZoteroContext': True,
            'referenceIds': ["item-123"],
            'contextType': 'analysis'
        }
        
        # Mock database query
        self.mock_db.query.return_value.filter.return_value.first.return_value = self.sample_item
        
        enhanced_content, references = await self.service.inject_reference_context(
            content, self.user_id, self.mock_db, options
        )
        
        assert len(references) == 1
        assert references[0]['id'] == "item-123"
        assert "Papers for analysis:" in enhanced_content
    
    def test_build_context_info(self):
        """Test building context information for AI"""
        references = [{
            'title': 'Machine Learning in Healthcare',
            'creators': ['John Smith', 'Jane Doe'],
            'year': 2023,
            'publicationTitle': 'Journal of Medical AI'
        }]
        
        context_info = self.service._build_context_info(references, 'research')
        
        expected = (
            "Research context from referenced papers:\n"
            "- Machine Learning in Healthcare by John Smith, Jane Doe (2023) - Journal of Medical AI"
        )
        assert context_info == expected
    
    def test_process_ai_response(self):
        """Test processing AI response to add reference links"""
        response = "According to Smith2023, machine learning shows promise in healthcare applications."
        references = [{
            'id': 'item-123',
            'title': 'Machine Learning in Healthcare',
            'creators': ['John Smith'],
            'citationKey': 'Smith2023'
        }]
        
        processed = self.service.process_ai_response(response, references)
        
        assert "[@Machine Learning in Healthcare](zotero:item-123)" in processed
    
    @pytest.mark.asyncio
    async def test_get_relevant_references(self):
        """Test getting relevant references for a topic"""
        topic = "machine learning"
        
        with patch.object(self.service.search_service, 'search_items') as mock_search:
            mock_search.return_value = {
                'items': [self.sample_item],
                'total_count': 1
            }
            
            references = await self.service.get_relevant_references(
                topic, self.user_id, self.mock_db, limit=5
            )
            
            assert len(references) == 1
            assert references[0]['title'] == "Machine Learning in Healthcare"
            mock_search.assert_called_once_with(
                user_id=self.user_id,
                query=topic,
                limit=5,
                db=self.mock_db
            )
    
    @pytest.mark.asyncio
    async def test_generate_citations_for_references(self):
        """Test generating citations for references"""
        references = [{
            'id': 'item-123',
            'title': 'Machine Learning in Healthcare',
            'creators': ['John Smith', 'Jane Doe'],
            'year': 2023
        }]
        
        with patch.object(self.service.citation_service, 'generate_citation') as mock_cite:
            mock_cite.return_value = {
                'bibliography': 'Smith, J., & Doe, J. (2023). Machine Learning in Healthcare.'
            }
            
            citations = await self.service.generate_citations_for_references(
                references, 'apa', self.user_id, self.mock_db
            )
            
            assert len(citations) == 1
            assert "Smith, J., & Doe, J. (2023)" in citations[0]
    
    @pytest.mark.asyncio
    async def test_create_research_summary(self):
        """Test creating research summary with references"""
        topic = "machine learning in healthcare"
        
        with patch.object(self.service, 'get_relevant_references') as mock_get_refs:
            mock_get_refs.return_value = [{
                'title': 'Machine Learning in Healthcare',
                'creators': ['John Smith', 'Jane Doe'],
                'year': 2023
            }]
            
            result = await self.service.create_research_summary(
                topic, self.user_id, self.mock_db
            )
            
            assert 'summary' in result
            assert 'references' in result
            assert topic in result['summary']
            assert "1 references from your Zotero library" in result['summary']
    
    def test_build_research_summary(self):
        """Test building research summary from references"""
        topic = "AI in Medicine"
        references = [
            {
                'title': 'Machine Learning in Healthcare',
                'creators': ['John Smith', 'Jane Doe'],
                'year': 2023
            },
            {
                'title': 'Deep Learning for Medical Diagnosis',
                'creators': ['Alice Johnson', 'Bob Wilson', 'Carol Brown'],
                'year': 2022
            }
        ]
        
        summary = self.service._build_research_summary(topic, references)
        
        assert "Research Summary: AI in Medicine" in summary
        assert "Based on 2 references" in summary
        assert "1. Machine Learning in Healthcare - John Smith, Jane Doe (2023)" in summary
        assert "2. Deep Learning for Medical Diagnosis - Alice Johnson, Bob Wilson et al. (2022)" in summary
    
    @pytest.mark.asyncio
    async def test_export_conversation_with_citations(self):
        """Test exporting conversation with citations"""
        messages = [
            {
                'role': 'user',
                'content': 'Tell me about machine learning',
                'timestamp': '2023-12-01T10:00:00',
                'references': [{
                    'id': 'item-123',
                    'title': 'Machine Learning in Healthcare',
                    'creators': ['John Smith'],
                    'year': 2023
                }]
            },
            {
                'role': 'assistant',
                'content': 'Machine learning has many applications in healthcare.',
                'timestamp': '2023-12-01T10:01:00'
            }
        ]
        
        with patch.object(self.service, 'generate_citations_for_references') as mock_cite:
            mock_cite.return_value = ['Smith, J. (2023). Machine Learning in Healthcare.']
            
            export_content = await self.service.export_conversation_with_citations(
                messages, self.user_id, self.mock_db, 'apa'
            )
            
            assert "# AI Scholar Conversation Export" in export_content
            assert "## User" in export_content
            assert "## AI Assistant" in export_content
            assert "## References" in export_content
            assert "Smith, J. (2023)" in export_content


class TestZoteroChatIntegrationEdgeCases:
    """Test edge cases and error handling"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.service = ZoteroChatIntegrationService()
        self.mock_db = Mock(spec=Session)
        self.user_id = "test-user-123"
    
    def test_extract_mentions_malformed(self):
        """Test extraction with malformed mention syntax"""
        content = "This has @[unclosed mention and @incomplete"
        
        mentions = self.service.extract_reference_mentions(content)
        
        assert len(mentions) == 0
    
    def test_convert_references_empty_creators(self):
        """Test conversion with items that have no creators"""
        item = ZoteroItem(
            id="item-123",
            title="Anonymous Paper",
            creators=[],
            date="2023"
        )
        
        references = self.service.convert_to_chat_references([item])
        
        assert len(references) == 1
        assert references[0]['creators'] == []
        assert references[0]['citationKey'] == "Unknown2023"
    
    def test_convert_references_no_date(self):
        """Test conversion with items that have no date"""
        item = ZoteroItem(
            id="item-123",
            title="Undated Paper",
            creators=[{"firstName": "John", "lastName": "Smith"}],
            date=None
        )
        
        references = self.service.convert_to_chat_references([item])
        
        assert len(references) == 1
        assert references[0]['year'] is None
        assert "Smith" in references[0]['citationKey']
    
    @pytest.mark.asyncio
    async def test_find_referenced_items_search_failure(self):
        """Test handling of search failures when finding referenced items"""
        mentions = ["Nonexistent Paper"]
        
        with patch.object(self.service.search_service, 'search_items') as mock_search:
            mock_search.side_effect = Exception("Search failed")
            
            items = await self.service.find_referenced_items(
                mentions, self.user_id, self.mock_db
            )
            
            assert len(items) == 0
    
    @pytest.mark.asyncio
    async def test_get_relevant_references_no_results(self):
        """Test getting relevant references when no results found"""
        topic = "nonexistent topic"
        
        with patch.object(self.service.search_service, 'search_items') as mock_search:
            mock_search.return_value = {'items': [], 'total_count': 0}
            
            references = await self.service.get_relevant_references(
                topic, self.user_id, self.mock_db
            )
            
            assert len(references) == 0
    
    def test_build_research_summary_no_references(self):
        """Test building research summary with no references"""
        topic = "Empty Topic"
        references = []
        
        summary = self.service._build_research_summary(topic, references)
        
        assert "No references found for topic: Empty Topic" in summary
    
    @pytest.mark.asyncio
    async def test_generate_citations_fallback(self):
        """Test citation generation fallback when service fails"""
        references = [{
            'id': 'item-123',
            'title': 'Test Paper',
            'creators': ['John Smith'],
            'year': 2023
        }]
        
        with patch.object(self.service.citation_service, 'generate_citation') as mock_cite:
            mock_cite.side_effect = Exception("Citation service failed")
            
            citations = await self.service.generate_citations_for_references(
                references, 'apa', self.user_id, self.mock_db
            )
            
            assert len(citations) == 1
            assert "John Smith (2023). Test Paper." in citations[0]