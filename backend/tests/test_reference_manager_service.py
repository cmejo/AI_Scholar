"""
Tests for Reference Manager Service

Tests the integration with Zotero, Mendeley, and EndNote reference managers.
"""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from backend.services.reference_manager_service import (
    ReferenceManagerService,
    ZoteroIntegration,
    MendeleyIntegration,
    EndNoteIntegration,
    ReferenceManagerType,
    BibliographicData,
    AuthCredentials,
    SyncResult
)

class TestBibliographicData:
    """Test BibliographicData model"""
    
    def test_bibliographic_data_creation(self):
        """Test creating BibliographicData instance"""
        data = BibliographicData(
            title="Test Article",
            authors=["John Doe", "Jane Smith"],
            journal="Test Journal",
            year=2023,
            doi="10.1000/test"
        )
        
        assert data.title == "Test Article"
        assert len(data.authors) == 2
        assert data.journal == "Test Journal"
        assert data.year == 2023
        assert data.doi == "10.1000/test"
        assert data.keywords == []
        assert data.tags == []
    
    def test_bibliographic_data_defaults(self):
        """Test default values for BibliographicData"""
        data = BibliographicData(title="Test", authors=[])
        
        assert data.keywords == []
        assert data.tags == []
        assert data.item_type == "article"
        assert data.abstract is None

class TestZoteroIntegration:
    """Test Zotero integration"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.zotero = ZoteroIntegration()
        self.mock_credentials = AuthCredentials(
            access_token="test_token",
            user_id="12345"
        )
    
    def test_get_authorization_url(self):
        """Test OAuth authorization URL generation"""
        url = asyncio.run(self.zotero.get_authorization_url(
            "client_id", "http://localhost/callback"
        ))
        
        assert "https://www.zotero.org/oauth/authorize" in url
        assert "client_id" in url
        assert "redirect_uri" in url
        assert "scope=read%20write" in url
    
    @patch('aiohttp.ClientSession.post')
    async def test_exchange_code_for_token(self, mock_post):
        """Test OAuth token exchange"""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'access_token': 'test_token',
            'token_type': 'Bearer',
            'userID': '12345'
        })
        mock_post.return_value.__aenter__.return_value = mock_response
        
        credentials = await self.zotero.exchange_code_for_token(
            "auth_code", "client_id", "client_secret", "redirect_uri"
        )
        
        assert credentials.access_token == "test_token"
        assert credentials.token_type == "Bearer"
        assert credentials.user_id == "12345"
    
    @patch('aiohttp.ClientSession.get')
    async def test_get_user_library(self, mock_get):
        """Test fetching user library"""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=[
            {
                'data': {
                    'title': 'Test Article',
                    'creators': [{'firstName': 'John', 'lastName': 'Doe'}],
                    'publicationTitle': 'Test Journal',
                    'date': '2023',
                    'DOI': '10.1000/test',
                    'abstractNote': 'Test abstract',
                    'itemType': 'journalArticle',
                    'tags': [{'tag': 'test'}]
                },
                'dateAdded': '2023-01-01T00:00:00Z',
                'dateModified': '2023-01-01T00:00:00Z'
            }
        ])
        mock_get.return_value.__aenter__.return_value = mock_response
        
        items = await self.zotero.get_user_library(self.mock_credentials)
        
        assert len(items) == 1
        assert items[0].title == "Test Article"
        assert items[0].authors == ["John Doe"]
        assert items[0].journal == "Test Journal"
        assert items[0].doi == "10.1000/test"
    
    def test_convert_zotero_item(self):
        """Test converting Zotero item to unified format"""
        zotero_item = {
            'data': {
                'title': 'Test Article',
                'creators': [{'firstName': 'John', 'lastName': 'Doe'}],
                'publicationTitle': 'Test Journal',
                'date': '2023',
                'DOI': '10.1000/test',
                'abstractNote': 'Test abstract',
                'itemType': 'journalArticle',
                'tags': [{'tag': 'test'}]
            },
            'dateAdded': '2023-01-01T00:00:00Z'
        }
        
        item = self.zotero._convert_zotero_item(zotero_item)
        
        assert item.title == "Test Article"
        assert item.authors == ["John Doe"]
        assert item.journal == "Test Journal"
        assert item.year == 2023
        assert item.doi == "10.1000/test"
        assert item.abstract == "Test abstract"
        assert item.tags == ["test"]
    
    def test_convert_to_zotero_format(self):
        """Test converting unified format to Zotero item"""
        item = BibliographicData(
            title="Test Article",
            authors=["John Doe"],
            journal="Test Journal",
            year=2023,
            doi="10.1000/test",
            abstract="Test abstract",
            tags=["test"]
        )
        
        zotero_item = self.zotero._convert_to_zotero_format(item)
        
        assert zotero_item['title'] == "Test Article"
        assert zotero_item['creators'][0]['firstName'] == "John"
        assert zotero_item['creators'][0]['lastName'] == "Doe"
        assert zotero_item['publicationTitle'] == "Test Journal"
        assert zotero_item['date'] == "2023"
        assert zotero_item['DOI'] == "10.1000/test"
        assert zotero_item['abstractNote'] == "Test abstract"
        assert zotero_item['tags'] == [{'tag': 'test'}]

class TestMendeleyIntegration:
    """Test Mendeley integration"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mendeley = MendeleyIntegration()
        self.mock_credentials = AuthCredentials(
            access_token="test_token",
            refresh_token="refresh_token"
        )
    
    def test_get_authorization_url(self):
        """Test OAuth authorization URL generation"""
        url = asyncio.run(self.mendeley.get_authorization_url(
            "client_id", "http://localhost/callback"
        ))
        
        assert "https://api.mendeley.com/oauth/authorize" in url
        assert "client_id" in url
        assert "redirect_uri" in url
        assert "scope=all" in url
    
    @patch('aiohttp.ClientSession.post')
    async def test_exchange_code_for_token(self, mock_post):
        """Test OAuth token exchange"""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'access_token': 'test_token',
            'refresh_token': 'refresh_token',
            'token_type': 'Bearer',
            'expires_in': 3600
        })
        mock_post.return_value.__aenter__.return_value = mock_response
        
        credentials = await self.mendeley.exchange_code_for_token(
            "auth_code", "client_id", "client_secret", "redirect_uri"
        )
        
        assert credentials.access_token == "test_token"
        assert credentials.refresh_token == "refresh_token"
        assert credentials.token_type == "Bearer"
        assert credentials.expires_in == 3600
    
    def test_convert_mendeley_item(self):
        """Test converting Mendeley item to unified format"""
        mendeley_item = {
            'title': 'Test Article',
            'authors': [{'first_name': 'John', 'last_name': 'Doe'}],
            'source': 'Test Journal',
            'year': 2023,
            'identifiers': {'doi': '10.1000/test'},
            'abstract': 'Test abstract',
            'keywords': ['test'],
            'type': 'journal',
            'tags': ['research'],
            'created': '2023-01-01T00:00:00Z'
        }
        
        item = self.mendeley._convert_mendeley_item(mendeley_item)
        
        assert item.title == "Test Article"
        assert item.authors == ["John Doe"]
        assert item.journal == "Test Journal"
        assert item.year == 2023
        assert item.doi == "10.1000/test"
        assert item.abstract == "Test abstract"
        assert item.keywords == ["test"]
        assert item.tags == ["research"]

class TestEndNoteIntegration:
    """Test EndNote integration"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.endnote = EndNoteIntegration()
    
    def test_supported_formats(self):
        """Test supported file formats"""
        assert '.enw' in self.endnote.supported_formats
        assert '.ris' in self.endnote.supported_formats
        assert '.xml' in self.endnote.supported_formats
    
    async def test_parse_ris_file(self):
        """Test parsing RIS format file"""
        ris_content = """TY  - JOUR
TI  - Test Article
AU  - Doe, John
AU  - Smith, Jane
JO  - Test Journal
PY  - 2023
DO  - 10.1000/test
AB  - Test abstract
KW  - test
KW  - research
ER  -

"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ris', delete=False) as f:
            f.write(ris_content)
            temp_path = f.name
        
        try:
            items = await self.endnote._parse_ris_file(temp_path)
            
            assert len(items) == 1
            assert items[0].title == "Test Article"
            assert "Doe, John" in items[0].authors
            assert "Smith, Jane" in items[0].authors
            assert items[0].journal == "Test Journal"
            assert items[0].year == 2023
            assert items[0].doi == "10.1000/test"
            assert items[0].abstract == "Test abstract"
            assert "test" in items[0].keywords
            assert "research" in items[0].keywords
        finally:
            os.unlink(temp_path)
    
    async def test_export_to_ris(self):
        """Test exporting to RIS format"""
        items = [
            BibliographicData(
                title="Test Article",
                authors=["John Doe", "Jane Smith"],
                journal="Test Journal",
                year=2023,
                doi="10.1000/test",
                abstract="Test abstract",
                keywords=["test", "research"]
            )
        ]
        
        with tempfile.NamedTemporaryFile(suffix='.ris', delete=False) as f:
            temp_path = f.name
        
        try:
            success = await self.endnote._export_to_ris(items, temp_path)
            assert success
            
            # Verify file content
            with open(temp_path, 'r') as f:
                content = f.read()
                assert "TY  - JOUR" in content
                assert "TI  - Test Article" in content
                assert "AU  - John Doe" in content
                assert "AU  - Jane Smith" in content
                assert "JO  - Test Journal" in content
                assert "PY  - 2023" in content
                assert "DO  - 10.1000/test" in content
                assert "AB  - Test abstract" in content
                assert "KW  - test" in content
                assert "KW  - research" in content
                assert "ER  -" in content
        finally:
            os.unlink(temp_path)
    
    def test_map_ris_type(self):
        """Test RIS type mapping"""
        assert self.endnote._map_ris_type("JOUR") == "article"
        assert self.endnote._map_ris_type("BOOK") == "book"
        assert self.endnote._map_ris_type("CHAP") == "chapter"
        assert self.endnote._map_ris_type("CONF") == "conference"
        assert self.endnote._map_ris_type("THES") == "thesis"
        assert self.endnote._map_ris_type("RPRT") == "report"
        assert self.endnote._map_ris_type("UNKNOWN") == "article"  # default
    
    def test_map_to_ris_type(self):
        """Test mapping to RIS type"""
        assert self.endnote._map_to_ris_type("article") == "JOUR"
        assert self.endnote._map_to_ris_type("book") == "BOOK"
        assert self.endnote._map_to_ris_type("chapter") == "CHAP"
        assert self.endnote._map_to_ris_type("conference") == "CONF"
        assert self.endnote._map_to_ris_type("thesis") == "THES"
        assert self.endnote._map_to_ris_type("report") == "RPRT"
        assert self.endnote._map_to_ris_type("unknown") == "JOUR"  # default

class TestReferenceManagerService:
    """Test unified reference manager service"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.service = ReferenceManagerService()
        self.mock_credentials = AuthCredentials(
            access_token="test_token",
            user_id="12345"
        )
    
    def test_get_supported_managers(self):
        """Test getting supported managers"""
        managers = self.service.get_supported_managers()
        
        assert "zotero" in managers
        assert "mendeley" in managers
        assert "endnote" in managers
        assert len(managers) == 3
    
    async def test_get_authorization_url_zotero(self):
        """Test getting authorization URL for Zotero"""
        with patch.object(self.service.zotero, 'get_authorization_url') as mock_auth:
            mock_auth.return_value = "https://test.url"
            
            url = await self.service.get_authorization_url(
                ReferenceManagerType.ZOTERO, "client_id", "redirect_uri"
            )
            
            assert url == "https://test.url"
            mock_auth.assert_called_once_with("client_id", "redirect_uri")
    
    async def test_get_authorization_url_endnote_error(self):
        """Test error when getting authorization URL for EndNote"""
        with pytest.raises(ValueError, match="EndNote does not support OAuth"):
            await self.service.get_authorization_url(
                ReferenceManagerType.ENDNOTE, "client_id", "redirect_uri"
            )
    
    async def test_sync_library_success(self):
        """Test successful library synchronization"""
        mock_items = [
            BibliographicData(title="Test 1", authors=["Author 1"]),
            BibliographicData(title="Test 2", authors=["Author 2"])
        ]
        
        with patch.object(self.service.zotero, 'get_user_library') as mock_sync:
            mock_sync.return_value = mock_items
            
            result = await self.service.sync_library(
                ReferenceManagerType.ZOTERO, self.mock_credentials
            )
            
            assert result.success is True
            assert result.items_synced == 2
            assert result.total_items == 2
            assert len(result.errors) == 0
    
    async def test_sync_library_error(self):
        """Test library synchronization error handling"""
        with patch.object(self.service.zotero, 'get_user_library') as mock_sync:
            mock_sync.side_effect = Exception("API Error")
            
            result = await self.service.sync_library(
                ReferenceManagerType.ZOTERO, self.mock_credentials
            )
            
            assert result.success is False
            assert result.items_synced == 0
            assert result.total_items == 0
            assert "API Error" in result.errors
    
    async def test_sync_library_endnote(self):
        """Test EndNote library synchronization"""
        mock_items = [BibliographicData(title="Test", authors=["Author"])]
        
        with patch.object(self.service.endnote, 'import_from_file') as mock_import:
            mock_import.return_value = mock_items
            
            result = await self.service.sync_library(
                ReferenceManagerType.ENDNOTE, file_path="test.ris"
            )
            
            assert result.success is True
            assert result.items_synced == 1
            mock_import.assert_called_once_with("test.ris")
    
    async def test_add_item_success(self):
        """Test successful item addition"""
        item = BibliographicData(title="Test", authors=["Author"])
        
        with patch.object(self.service.zotero, 'add_item_to_library') as mock_add:
            mock_add.return_value = True
            
            success = await self.service.add_item(
                ReferenceManagerType.ZOTERO, item, self.mock_credentials
            )
            
            assert success is True
            mock_add.assert_called_once_with(self.mock_credentials, item)
    
    async def test_export_library(self):
        """Test library export"""
        items = [BibliographicData(title="Test", authors=["Author"])]
        
        with patch.object(self.service.endnote, 'export_to_file') as mock_export:
            mock_export.return_value = True
            
            success = await self.service.export_library(items, "test.ris")
            
            assert success is True
            mock_export.assert_called_once_with(items, "test.ris", "ris")
    
    def test_validate_credentials(self):
        """Test credential validation"""
        valid_creds = AuthCredentials(access_token="test_token")
        invalid_creds = AuthCredentials(access_token="")
        
        assert self.service.validate_credentials(valid_creds) is True
        assert self.service.validate_credentials(invalid_creds) is False

if __name__ == "__main__":
    pytest.main([__file__])