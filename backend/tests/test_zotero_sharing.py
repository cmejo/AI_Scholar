"""
Tests for Zotero Sharing and Export Service

Tests the export and sharing capabilities for Zotero-integrated content.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session

from ..services.zotero.zotero_sharing_service import ZoteroSharingService
from ..models.zotero_models import ZoteroItem


class TestZoteroSharingService:
    """Test suite for ZoteroSharingService"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.service = ZoteroSharingService()
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
        
        # Sample messages
        self.sample_messages = [
            {
                'role': 'user',
                'content': 'Tell me about machine learning in healthcare',
                'timestamp': '2023-12-01T10:00:00',
                'references': [
                    {
                        'id': 'item-123',
                        'title': 'Machine Learning in Healthcare',
                        'creators': ['John Smith', 'Jane Doe'],
                        'year': 2023,
                        'publicationTitle': 'Journal of Medical AI'
                    }
                ]
            },
            {
                'role': 'assistant',
                'content': 'Machine learning has many applications in healthcare...',
                'timestamp': '2023-12-01T10:01:00'
            }
        ]
    
    def test_get_export_formats(self):
        """Test getting available export formats"""
        formats = self.service.get_export_formats()
        
        assert len(formats) > 0
        
        # Check for expected formats
        format_ids = [f['id'] for f in formats]
        assert 'markdown' in format_ids
        assert 'html' in format_ids
        assert 'pdf' in format_ids
        assert 'bibtex' in format_ids
        
        # Check format structure
        markdown_format = next(f for f in formats if f['id'] == 'markdown')
        assert markdown_format['name'] == 'Markdown'
        assert markdown_format['extension'] == 'md'
        assert markdown_format['mimeType'] == 'text/markdown'
        assert 'description' in markdown_format
    
    @pytest.mark.asyncio
    async def test_export_conversation_markdown(self):
        """Test exporting conversation as Markdown"""
        options = {
            'format': 'markdown',
            'includeCitations': True,
            'citationStyle': 'apa',
            'includeMetadata': True,
            'includeTimestamps': True,
            'includeReferences': True
        }
        
        # Mock citation service
        with patch.object(self.service, '_generate_citations') as mock_citations:
            mock_citations.return_value = ['Smith, J., & Doe, J. (2023). Machine Learning in Healthcare.']
            
            result = await self.service.export_conversation(
                self.sample_messages, options, self.user_id, self.mock_db
            )
            
            assert 'content' in result
            assert 'filename' in result
            assert 'mimeType' in result
            
            content = result['content']
            assert '# AI Scholar Conversation Export' in content
            assert '## User' in content
            assert '## AI Assistant' in content
            assert 'Tell me about machine learning in healthcare' in content
            assert '## References' in content
            assert 'Machine Learning in Healthcare' in content
    
    @pytest.mark.asyncio
    async def test_export_conversation_html(self):
        """Test exporting conversation as HTML"""
        options = {
            'format': 'html',
            'includeCitations': True,
            'includeMetadata': True
        }
        
        result = await self.service.export_conversation(
            self.sample_messages, options, self.user_id, self.mock_db
        )
        
        assert result['mimeType'] == 'text/html'
        content = result['content']
        assert '<!DOCTYPE html>' in content
        assert '<html lang="en">' in content
        assert '<h1>' in content
        assert '<h2>' in content
    
    @pytest.mark.asyncio
    async def test_export_conversation_minimal_options(self):
        """Test exporting conversation with minimal options"""
        options = {
            'format': 'markdown',
            'includeCitations': False,
            'includeMetadata': False,
            'includeTimestamps': False,
            'includeReferences': False
        }
        
        result = await self.service.export_conversation(
            self.sample_messages, options, self.user_id, self.mock_db
        )
        
        content = result['content']
        assert '# AI Scholar Conversation Export' in content
        assert '**Exported:**' not in content  # No metadata
        assert '## References' not in content  # No citations
        assert '**Referenced Papers:**' not in content  # No references
    
    @pytest.mark.asyncio
    async def test_share_reference(self):
        """Test sharing reference with other users"""
        reference_id = "item-123"
        shared_with = ["user-456", "user-789"]
        permissions = {
            'canView': True,
            'canComment': True,
            'canEdit': False,
            'canShare': False
        }
        note = "Sharing this interesting paper"
        
        result = await self.service.share_reference(
            reference_id, shared_with, permissions, self.user_id, self.mock_db, note
        )
        
        assert result['referenceId'] == reference_id
        assert result['sharedBy'] == self.user_id
        assert result['sharedWith'] == shared_with
        assert result['permissions'] == permissions
        assert result['note'] == note
        assert 'id' in result
        assert 'sharedAt' in result
    
    @pytest.mark.asyncio
    async def test_create_reference_collection(self):
        """Test creating reference collection"""
        name = "Machine Learning Papers"
        description = "Collection of papers on ML in healthcare"
        reference_ids = ["item-123"]
        tags = ["machine-learning", "healthcare"]
        
        # Mock database query
        self.mock_db.query.return_value.filter.return_value.first.return_value = self.sample_item
        
        result = await self.service.create_reference_collection(
            name, description, reference_ids, self.user_id, self.mock_db, 
            is_public=False, tags=tags
        )
        
        assert result['name'] == name
        assert result['description'] == description
        assert result['createdBy'] == self.user_id
        assert result['isPublic'] == False
        assert result['tags'] == tags
        assert len(result['references']) == 1
        assert result['references'][0]['title'] == "Machine Learning in Healthcare"
        assert 'id' in result
        assert 'createdAt' in result
        assert 'updatedAt' in result
    
    @pytest.mark.asyncio
    async def test_export_project_markdown(self):
        """Test exporting project as Markdown"""
        project_data = {
            'title': 'ML Research Project',
            'description': 'Research on machine learning applications',
            'references': [
                {
                    'id': 'item-123',
                    'title': 'Machine Learning in Healthcare',
                    'creators': ['John Smith', 'Jane Doe'],
                    'year': 2023,
                    'publicationTitle': 'Journal of Medical AI'
                }
            ],
            'notes': [
                {
                    'title': 'Research Notes',
                    'content': 'These are my research notes...',
                    'tags': ['research', 'notes']
                }
            ]
        }
        
        options = {
            'format': 'markdown',
            'includeNotes': True,
            'includeReferences': True,
            'includeBibliography': True,
            'citationStyle': 'apa'
        }
        
        # Mock citation service
        with patch.object(self.service, '_generate_citations') as mock_citations:
            mock_citations.return_value = ['Smith, J., & Doe, J. (2023). Machine Learning in Healthcare.']
            
            result = await self.service.export_project(
                project_data, options, self.user_id, self.mock_db
            )
            
            content = result['content']
            assert '# ML Research Project' in content
            assert 'Research on machine learning applications' in content
            assert '## References' in content
            assert '## Research Notes' in content
            assert '## Bibliography' in content
            assert 'Machine Learning in Healthcare' in content
    
    def test_generate_shareable_link_public(self):
        """Test generating shareable link for public collection"""
        collection_id = "collection-123"
        base_url = "https://test.com"
        
        link = self.service.generate_shareable_link(collection_id, True, base_url)
        
        expected = f"{base_url}/shared/collection/{collection_id}"
        assert link == expected
    
    def test_generate_shareable_link_private(self):
        """Test generating shareable link for private collection"""
        collection_id = "collection-123"
        base_url = "https://test.com"
        
        link = self.service.generate_shareable_link(collection_id, False, base_url)
        
        assert f"{base_url}/shared/collection/{collection_id}?token=" in link
        assert len(link.split('token=')[1]) == 32  # Token length
    
    def test_convert_item_to_reference(self):
        """Test converting Zotero item to reference format"""
        reference = self.service._convert_item_to_reference(self.sample_item)
        
        assert reference['id'] == "item-123"
        assert reference['title'] == "Machine Learning in Healthcare"
        assert reference['creators'] == ["John Smith", "Jane Doe"]
        assert reference['year'] == 2023
        assert reference['publicationTitle'] == "Journal of Medical AI"
        assert reference['relevance'] == 1.0
        assert reference['citationKey'] == "Smith2023"
        assert reference['abstractNote'] == "This paper explores machine learning applications in healthcare."
    
    def test_generate_citation_key(self):
        """Test generating citation key"""
        creators = ["John Smith", "Jane Doe"]
        year = 2023
        
        citation_key = self.service._generate_citation_key(creators, year)
        
        assert citation_key == "Smith2023"
    
    def test_generate_citation_key_no_creators(self):
        """Test generating citation key with no creators"""
        creators = []
        year = 2023
        
        citation_key = self.service._generate_citation_key(creators, year)
        
        assert citation_key == "Unknown2023"
    
    def test_remove_duplicate_references(self):
        """Test removing duplicate references"""
        references = [
            {'id': 'item-123', 'title': 'Paper 1'},
            {'id': 'item-456', 'title': 'Paper 2'},
            {'id': 'item-123', 'title': 'Paper 1 Duplicate'},  # Duplicate
            {'id': 'item-789', 'title': 'Paper 3'}
        ]
        
        unique_refs = self.service._remove_duplicate_references(references)
        
        assert len(unique_refs) == 3
        ids = [ref['id'] for ref in unique_refs]
        assert 'item-123' in ids
        assert 'item-456' in ids
        assert 'item-789' in ids
    
    def test_get_format_extension(self):
        """Test getting format extensions"""
        assert self.service._get_format_extension('markdown') == 'md'
        assert self.service._get_format_extension('html') == 'html'
        assert self.service._get_format_extension('pdf') == 'pdf'
        assert self.service._get_format_extension('unknown') == 'txt'
    
    def test_generate_secure_token(self):
        """Test generating secure token"""
        token = self.service._generate_secure_token()
        
        assert len(token) == 32
        assert token.isalnum()


class TestZoteroSharingServiceEdgeCases:
    """Test edge cases and error handling"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.service = ZoteroSharingService()
        self.mock_db = Mock(spec=Session)
        self.user_id = "test-user-123"
    
    @pytest.mark.asyncio
    async def test_export_conversation_empty_messages(self):
        """Test exporting conversation with empty messages"""
        messages = []
        options = {'format': 'markdown'}
        
        result = await self.service.export_conversation(
            messages, options, self.user_id, self.mock_db
        )
        
        content = result['content']
        assert '# AI Scholar Conversation Export' in content
        assert '## User' not in content
        assert '## Assistant' not in content
    
    @pytest.mark.asyncio
    async def test_export_conversation_no_references(self):
        """Test exporting conversation with no references"""
        messages = [
            {
                'role': 'user',
                'content': 'Hello',
                'timestamp': '2023-12-01T10:00:00'
            }
        ]
        options = {'format': 'markdown', 'includeCitations': True}
        
        result = await self.service.export_conversation(
            messages, options, self.user_id, self.mock_db
        )
        
        content = result['content']
        assert '## References' not in content
    
    @pytest.mark.asyncio
    async def test_create_collection_missing_references(self):
        """Test creating collection with missing references"""
        name = "Test Collection"
        description = "Test description"
        reference_ids = ["nonexistent-item"]
        
        # Mock database query returning None
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = await self.service.create_reference_collection(
            name, description, reference_ids, self.user_id, self.mock_db
        )
        
        assert result['name'] == name
        assert len(result['references']) == 0  # No references found
    
    @pytest.mark.asyncio
    async def test_generate_citations_service_failure(self):
        """Test citation generation when service fails"""
        references = [
            {
                'id': 'item-123',
                'title': 'Test Paper',
                'creators': ['Author'],
                'year': 2023
            }
        ]
        
        # Mock citation service failure
        with patch.object(self.service.citation_service, 'generate_citation') as mock_cite:
            mock_cite.side_effect = Exception("Citation service failed")
            
            citations = await self.service._generate_citations(
                references, 'apa', self.user_id, self.mock_db
            )
            
            # Should fallback to simple format
            assert len(citations) == 1
            assert "Author (2023). Test Paper." in citations[0]
    
    def test_convert_item_no_creators(self):
        """Test converting item with no creators"""
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
        """Test converting item with no date"""
        item = ZoteroItem(
            id="item-123",
            title="Undated Paper",
            creators=[{"firstName": "John", "lastName": "Smith"}],
            date=None
        )
        
        reference = self.service._convert_item_to_reference(item)
        
        assert reference['year'] is None
        assert "Smith" in reference['citationKey']