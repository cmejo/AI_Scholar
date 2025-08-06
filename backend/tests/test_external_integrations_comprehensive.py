"""
Comprehensive test suite for external integrations including API testing and service validation.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import json
from datetime import datetime, timedelta

from services.reference_manager_service import ReferenceManagerService
from services.academic_database_service import AcademicDatabaseService
from services.note_taking_integration_service import NoteTakingIntegrationService
from services.writing_tools_service import WritingToolsService


class TestReferenceManagerIntegrations:
    """Test suite for reference manager integrations (Zotero, Mendeley, EndNote)."""
    
    @pytest.fixture
    def reference_manager_service(self):
        return ReferenceManagerService()
    
    @pytest.fixture
    def mock_zotero_credentials(self):
        return {
            "api_key": "test_zotero_api_key",
            "user_id": "12345",
            "library_type": "user"
        }
    
    @pytest.fixture
    def mock_mendeley_credentials(self):
        return {
            "access_token": "test_mendeley_token",
            "refresh_token": "test_refresh_token",
            "client_id": "test_client_id"
        }
    
    @pytest.fixture
    def mock_bibliography_data(self):
        return [
            {
                "id": "item1",
                "title": "Machine Learning in Research",
                "authors": ["Smith, J.", "Doe, A."],
                "journal": "AI Research Journal",
                "year": 2023,
                "doi": "10.1000/test.doi.1"
            },
            {
                "id": "item2",
                "title": "Deep Learning Applications",
                "authors": ["Johnson, B."],
                "journal": "Neural Networks Today",
                "year": 2023,
                "doi": "10.1000/test.doi.2"
            }
        ]

    @pytest.mark.asyncio
    async def test_zotero_library_sync(self, reference_manager_service, mock_zotero_credentials, mock_bibliography_data):
        """Test Zotero library synchronization."""
        with patch.object(reference_manager_service, '_fetch_zotero_items') as mock_fetch:
            mock_fetch.return_value = mock_bibliography_data
            
            result = await reference_manager_service.sync_zotero_library(mock_zotero_credentials)
            
            assert result["success"] is True
            assert result["synced_items"] == 2
            assert result["library_type"] == "user"
            assert len(result["items"]) == 2
    
    @pytest.mark.asyncio
    async def test_mendeley_document_sync(self, reference_manager_service, mock_mendeley_credentials):
        """Test Mendeley document and annotation synchronization."""
        mock_documents = [
            {
                "id": "doc1",
                "title": "Research Paper 1",
                "annotations": [
                    {"id": "ann1", "text": "Important finding", "page": 1}
                ]
            }
        ]
        
        with patch.object(reference_manager_service, '_fetch_mendeley_documents') as mock_fetch:
            mock_fetch.return_value = mock_documents
            
            result = await reference_manager_service.sync_mendeley_documents(mock_mendeley_credentials)
            
            assert result["success"] is True
            assert result["synced_documents"] == 1
            assert result["synced_annotations"] == 1
    
    @pytest.mark.asyncio
    async def test_endnote_citation_management(self, reference_manager_service):
        """Test EndNote citation and bibliography management."""
        endnote_credentials = {
            "library_path": "/path/to/endnote/library.enl",
            "sync_token": "test_sync_token"
        }
        
        citation_data = {
            "style": "APA",
            "references": ["item1", "item2"],
            "format": "bibliography"
        }
        
        with patch.object(reference_manager_service, '_generate_endnote_citation') as mock_cite:
            mock_cite.return_value = {
                "citation": "Smith, J., & Doe, A. (2023). Machine Learning in Research. AI Research Journal.",
                "formatted": True
            }
            
            result = await reference_manager_service.generate_endnote_citation(
                endnote_credentials, citation_data
            )
            
            assert result["formatted"] is True
            assert "citation" in result
            assert "Smith, J." in result["citation"]
    
    @pytest.mark.asyncio
    async def test_cross_platform_bibliography_sync(self, reference_manager_service):
        """Test unified bibliography synchronization across platforms."""
        platforms = ["zotero", "mendeley", "endnote"]
        
        for platform in platforms:
            credentials = {
                "platform": platform,
                "api_key": f"test_{platform}_key"
            }
            
            result = await reference_manager_service.sync_bibliography(credentials)
            
            assert result["success"] is True
            assert result["platform"] == platform
            assert "synced_items" in result
    
    @pytest.mark.asyncio
    async def test_reference_deduplication(self, reference_manager_service, mock_bibliography_data):
        """Test automatic reference deduplication across platforms."""
        # Add duplicate with slight variation
        duplicate_data = mock_bibliography_data + [
            {
                "id": "item1_duplicate",
                "title": "Machine Learning in Research",  # Same title
                "authors": ["Smith, J.", "Doe, A."],  # Same authors
                "journal": "AI Research Journal",
                "year": 2023,
                "doi": "10.1000/test.doi.1"  # Same DOI
            }
        ]
        
        result = await reference_manager_service.deduplicate_references(duplicate_data)
        
        assert result["duplicates_found"] == 1
        assert result["deduplicated_count"] == 2  # Original 2 items
        assert len(result["unique_references"]) == 2


class TestAcademicDatabaseIntegrations:
    """Test suite for academic database integrations (PubMed, arXiv, Google Scholar)."""
    
    @pytest.fixture
    def academic_db_service(self):
        return AcademicDatabaseService()
    
    @pytest.mark.asyncio
    async def test_pubmed_search_integration(self, academic_db_service):
        """Test PubMed API integration and search functionality."""
        search_query = "machine learning healthcare"
        
        mock_pubmed_results = {
            "papers": [
                {
                    "pmid": "12345678",
                    "title": "Machine Learning in Healthcare Applications",
                    "authors": ["Smith, J.", "Johnson, A."],
                    "abstract": "This paper explores ML applications in healthcare...",
                    "journal": "Medical AI Journal",
                    "pub_date": "2023-01-15"
                }
            ],
            "total_results": 1
        }
        
        with patch.object(academic_db_service, '_search_pubmed') as mock_search:
            mock_search.return_value = mock_pubmed_results
            
            result = await academic_db_service.search_pubmed(search_query)
            
            assert result["success"] is True
            assert result["total_results"] == 1
            assert len(result["papers"]) == 1
            assert result["papers"][0]["pmid"] == "12345678"
    
    @pytest.mark.asyncio
    async def test_arxiv_paper_discovery(self, academic_db_service):
        """Test arXiv API integration for paper discovery."""
        search_query = "quantum computing"
        
        mock_arxiv_results = {
            "papers": [
                {
                    "arxiv_id": "2301.12345",
                    "title": "Advances in Quantum Computing",
                    "authors": ["Quantum, A.", "Computing, B."],
                    "abstract": "Recent advances in quantum computing...",
                    "categories": ["quant-ph", "cs.ET"],
                    "submitted": "2023-01-20"
                }
            ],
            "total_results": 1
        }
        
        with patch.object(academic_db_service, '_search_arxiv') as mock_search:
            mock_search.return_value = mock_arxiv_results
            
            result = await academic_db_service.search_arxiv(search_query)
            
            assert result["success"] is True
            assert result["total_results"] == 1
            assert result["papers"][0]["arxiv_id"] == "2301.12345"
    
    @pytest.mark.asyncio
    async def test_google_scholar_scraping(self, academic_db_service):
        """Test Google Scholar integration with rate limiting."""
        search_query = "artificial intelligence ethics"
        
        mock_scholar_results = {
            "papers": [
                {
                    "title": "Ethics in Artificial Intelligence",
                    "authors": ["Ethics, A.I."],
                    "venue": "AI Ethics Conference",
                    "year": "2023",
                    "citations": 42,
                    "url": "https://example.com/paper1"
                }
            ],
            "total_results": 1,
            "rate_limited": False
        }
        
        with patch.object(academic_db_service, '_search_google_scholar') as mock_search:
            mock_search.return_value = mock_scholar_results
            
            result = await academic_db_service.search_google_scholar(search_query)
            
            assert result["success"] is True
            assert result["rate_limited"] is False
            assert result["papers"][0]["citations"] == 42
    
    @pytest.mark.asyncio
    async def test_unified_academic_search(self, academic_db_service):
        """Test unified search across multiple academic databases."""
        search_query = "neural networks"
        databases = ["pubmed", "arxiv", "google_scholar"]
        
        for db in databases:
            result = await academic_db_service.unified_search(search_query, databases=[db])
            
            assert result["success"] is True
            assert db in result["sources"]
            assert "papers" in result
    
    @pytest.mark.asyncio
    async def test_metadata_extraction_accuracy(self, academic_db_service):
        """Test accuracy of paper metadata extraction."""
        paper_url = "https://example.com/paper.pdf"
        
        expected_metadata = {
            "title": "Test Paper Title",
            "authors": ["Author, A.", "Author, B."],
            "abstract": "This is a test abstract...",
            "keywords": ["test", "paper", "metadata"],
            "doi": "10.1000/test.doi"
        }
        
        with patch.object(academic_db_service, '_extract_paper_metadata') as mock_extract:
            mock_extract.return_value = expected_metadata
            
            result = await academic_db_service.extract_paper_metadata(paper_url)
            
            assert result["title"] == expected_metadata["title"]
            assert len(result["authors"]) == 2
            assert result["doi"] == expected_metadata["doi"]


class TestNoteTakingIntegrations:
    """Test suite for note-taking app integrations (Obsidian, Notion, Roam Research)."""
    
    @pytest.fixture
    def note_taking_service(self):
        return NoteTakingIntegrationService()
    
    @pytest.mark.asyncio
    async def test_obsidian_vault_sync(self, note_taking_service):
        """Test Obsidian vault synchronization with markdown preservation."""
        vault_config = {
            "vault_path": "/path/to/obsidian/vault",
            "sync_settings": {
                "preserve_links": True,
                "sync_attachments": True,
                "bidirectional": True
            }
        }
        
        mock_vault_data = {
            "notes": [
                {
                    "filename": "Research Notes.md",
                    "content": "# Research Notes\n\n[[Linked Note]] - Important finding",
                    "links": ["Linked Note"],
                    "tags": ["#research", "#important"]
                }
            ],
            "attachments": ["image1.png", "document1.pdf"]
        }
        
        with patch.object(note_taking_service, '_sync_obsidian_vault') as mock_sync:
            mock_sync.return_value = {
                "synced": True,
                "notes_synced": 1,
                "links_preserved": True,
                "attachments_synced": 2
            }
            
            result = await note_taking_service.sync_obsidian_vault(vault_config)
            
            assert result["synced"] is True
            assert result["links_preserved"] is True
            assert result["attachments_synced"] == 2
    
    @pytest.mark.asyncio
    async def test_notion_workspace_integration(self, note_taking_service):
        """Test Notion workspace integration with database sync."""
        notion_config = {
            "api_token": "test_notion_token",
            "workspace_id": "test_workspace",
            "databases": ["research_papers", "notes", "tasks"]
        }
        
        mock_notion_data = {
            "databases": {
                "research_papers": [
                    {
                        "id": "page1",
                        "title": "Paper Analysis",
                        "properties": {
                            "Status": "In Progress",
                            "Tags": ["AI", "ML"]
                        }
                    }
                ]
            }
        }
        
        with patch.object(note_taking_service, '_sync_notion_workspace') as mock_sync:
            mock_sync.return_value = {
                "synced": True,
                "databases_synced": 3,
                "pages_synced": 1
            }
            
            result = await note_taking_service.sync_notion_workspace(notion_config)
            
            assert result["synced"] is True
            assert result["databases_synced"] == 3
    
    @pytest.mark.asyncio
    async def test_roam_research_graph_sync(self, note_taking_service):
        """Test Roam Research graph synchronization with block-level integration."""
        roam_config = {
            "graph_name": "research_graph",
            "api_token": "test_roam_token",
            "sync_blocks": True
        }
        
        mock_roam_data = {
            "blocks": [
                {
                    "uid": "block1",
                    "string": "Important research finding",
                    "children": [
                        {"uid": "child1", "string": "Supporting evidence"}
                    ],
                    "refs": ["[[Research Topic]]"]
                }
            ]
        }
        
        with patch.object(note_taking_service, '_sync_roam_graph') as mock_sync:
            mock_sync.return_value = {
                "synced": True,
                "blocks_synced": 2,
                "references_preserved": True
            }
            
            result = await note_taking_service.sync_roam_graph(roam_config)
            
            assert result["synced"] is True
            assert result["blocks_synced"] == 2
            assert result["references_preserved"] is True
    
    @pytest.mark.asyncio
    async def test_bidirectional_knowledge_graph_sync(self, note_taking_service):
        """Test bidirectional knowledge graph synchronization across platforms."""
        platforms = ["obsidian", "notion", "roam"]
        
        knowledge_graph_data = {
            "nodes": [
                {"id": "concept1", "label": "Machine Learning", "type": "concept"},
                {"id": "paper1", "label": "ML Paper", "type": "document"}
            ],
            "edges": [
                {"source": "paper1", "target": "concept1", "relation": "discusses"}
            ]
        }
        
        for platform in platforms:
            result = await note_taking_service.sync_knowledge_graph(platform, knowledge_graph_data)
            
            assert result["synced"] is True
            assert result["platform"] == platform
            assert result["nodes_synced"] == 2
            assert result["edges_synced"] == 1


class TestWritingToolIntegrations:
    """Test suite for writing tool integrations (Grammarly, LaTeX editors)."""
    
    @pytest.fixture
    def writing_tools_service(self):
        return WritingToolsService()
    
    @pytest.mark.asyncio
    async def test_grammarly_integration(self, writing_tools_service):
        """Test Grammarly API integration for grammar and style checking."""
        text_to_check = "This is a test sentence with some grammer mistakes."
        
        mock_grammarly_response = {
            "suggestions": [
                {
                    "id": "1",
                    "text": "grammer",
                    "replacement": "grammar",
                    "type": "spelling",
                    "position": {"start": 45, "end": 52}
                }
            ],
            "score": 85
        }
        
        with patch.object(writing_tools_service, '_check_with_grammarly') as mock_check:
            mock_check.return_value = mock_grammarly_response
            
            result = await writing_tools_service.check_grammar(text_to_check)
            
            assert result["score"] == 85
            assert len(result["suggestions"]) == 1
            assert result["suggestions"][0]["type"] == "spelling"
    
    @pytest.mark.asyncio
    async def test_latex_editor_integration(self, writing_tools_service):
        """Test LaTeX editor integration with compilation and preview."""
        latex_content = r"""
        \documentclass{article}
        \begin{document}
        \title{Test Document}
        \author{Test Author}
        \maketitle
        This is a test LaTeX document.
        \end{document}
        """
        
        mock_compilation_result = {
            "compiled": True,
            "pdf_generated": True,
            "errors": [],
            "warnings": [],
            "output_path": "/tmp/test_document.pdf"
        }
        
        with patch.object(writing_tools_service, '_compile_latex') as mock_compile:
            mock_compile.return_value = mock_compilation_result
            
            result = await writing_tools_service.compile_latex(latex_content)
            
            assert result["compiled"] is True
            assert result["pdf_generated"] is True
            assert len(result["errors"]) == 0
    
    @pytest.mark.asyncio
    async def test_collaborative_writing_sync(self, writing_tools_service):
        """Test collaborative writing features with external tool synchronization."""
        document_id = "collab_doc_123"
        collaborators = ["user1", "user2", "user3"]
        
        changes = [
            {
                "user": "user1",
                "timestamp": datetime.now().isoformat(),
                "type": "text_insert",
                "position": 100,
                "content": "Additional research findings"
            }
        ]
        
        result = await writing_tools_service.sync_collaborative_changes(
            document_id, changes, collaborators
        )
        
        assert result["synced"] is True
        assert result["changes_applied"] == 1
        assert len(result["notified_users"]) == 2  # Other collaborators
    
    @pytest.mark.asyncio
    async def test_document_export_formats(self, writing_tools_service):
        """Test document export to various writing platforms and formats."""
        document_content = {
            "title": "Research Paper",
            "content": "This is the main content of the research paper.",
            "metadata": {
                "authors": ["Author, A."],
                "keywords": ["research", "paper"]
            }
        }
        
        export_formats = ["docx", "pdf", "latex", "markdown", "html"]
        
        for format_type in export_formats:
            result = await writing_tools_service.export_document(document_content, format_type)
            
            assert result["exported"] is True
            assert result["format"] == format_type
            assert "export_path" in result or "export_data" in result


class TestIntegrationErrorHandling:
    """Test suite for integration error handling and resilience."""
    
    @pytest.fixture
    def reference_manager_service(self):
        return ReferenceManagerService()
    
    @pytest.mark.asyncio
    async def test_api_rate_limiting_handling(self, reference_manager_service):
        """Test handling of API rate limiting across integrations."""
        # Simulate rate limiting response
        with patch.object(reference_manager_service, '_make_api_request') as mock_request:
            mock_request.side_effect = [
                {"error": "rate_limited", "retry_after": 60},
                {"success": True, "data": []}  # Successful retry
            ]
            
            result = await reference_manager_service.sync_with_rate_limiting("zotero", {})
            
            assert result["success"] is True
            assert result["rate_limited"] is True
            assert result["retries"] == 1
    
    @pytest.mark.asyncio
    async def test_authentication_failure_recovery(self, reference_manager_service):
        """Test authentication failure recovery mechanisms."""
        expired_credentials = {
            "access_token": "expired_token",
            "refresh_token": "valid_refresh_token"
        }
        
        with patch.object(reference_manager_service, '_refresh_token') as mock_refresh:
            mock_refresh.return_value = {
                "access_token": "new_valid_token",
                "expires_in": 3600
            }
            
            result = await reference_manager_service.handle_auth_failure(expired_credentials)
            
            assert result["recovered"] is True
            assert result["new_token"] == "new_valid_token"
    
    @pytest.mark.asyncio
    async def test_service_unavailability_fallback(self, reference_manager_service):
        """Test fallback mechanisms when external services are unavailable."""
        with patch.object(reference_manager_service, '_check_service_health') as mock_health:
            mock_health.return_value = {"available": False, "error": "service_down"}
            
            result = await reference_manager_service.sync_with_fallback("mendeley", {})
            
            assert result["fallback_used"] is True
            assert result["cached_data_used"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])