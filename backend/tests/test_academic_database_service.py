"""
Tests for Academic Database Service

Tests the integration with PubMed, arXiv, and Google Scholar.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from backend.services.academic_database_service import (
    AcademicDatabaseService,
    PubMedConnector,
    ArXivConnector,
    GoogleScholarConnector,
    DatabaseType,
    SearchQuery,
    SearchResult,
    RateLimiter
)

class TestSearchResult:
    """Test SearchResult model"""
    
    def test_search_result_creation(self):
        """Test creating SearchResult instance"""
        result = SearchResult(
            title="Test Article",
            authors=["John Doe", "Jane Smith"],
            abstract="Test abstract",
            journal="Test Journal",
            year=2023,
            doi="10.1000/test",
            database="pubmed"
        )
        
        assert result.title == "Test Article"
        assert len(result.authors) == 2
        assert result.journal == "Test Journal"
        assert result.year == 2023
        assert result.doi == "10.1000/test"
        assert result.database == "pubmed"
        assert result.keywords == []
    
    def test_search_result_defaults(self):
        """Test default values for SearchResult"""
        result = SearchResult(title="Test", authors=[], database="test")
        
        assert result.keywords == []
        assert result.abstract is None
        assert result.citation_count is None

class TestSearchQuery:
    """Test SearchQuery model"""
    
    def test_search_query_creation(self):
        """Test creating SearchQuery instance"""
        query = SearchQuery(
            query="machine learning",
            max_results=50,
            author="John Doe",
            journal="Nature"
        )
        
        assert query.query == "machine learning"
        assert query.max_results == 50
        assert query.author == "John Doe"
        assert query.journal == "Nature"
        assert query.sort_by == "relevance"
    
    def test_search_query_defaults(self):
        """Test default values for SearchQuery"""
        query = SearchQuery(query="test")
        
        assert query.max_results == 20
        assert query.sort_by == "relevance"
        assert query.start_date is None
        assert query.end_date is None

class TestRateLimiter:
    """Test RateLimiter functionality"""
    
    def test_rate_limiter_creation(self):
        """Test creating RateLimiter instance"""
        limiter = RateLimiter(max_requests=5, time_window=10)
        
        assert limiter.max_requests == 5
        assert limiter.time_window == 10
        assert limiter.requests == []
    
    @pytest.mark.asyncio
    async def test_rate_limiter_no_wait_when_under_limit(self):
        """Test no waiting when under rate limit"""
        limiter = RateLimiter(max_requests=5, time_window=10)
        
        # Should not wait when no previous requests
        start_time = asyncio.get_event_loop().time()
        await limiter.wait_if_needed()
        end_time = asyncio.get_event_loop().time()
        
        # Should be very fast (no waiting)
        assert end_time - start_time < 0.1

class TestPubMedConnector:
    """Test PubMed integration"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.pubmed = PubMedConnector(email="test@example.com")
    
    def test_build_search_term(self):
        """Test building PubMed search terms"""
        query = SearchQuery(
            query="machine learning",
            author="John Doe",
            journal="Nature"
        )
        
        search_term = self.pubmed._build_search_term(query)
        
        assert "machine learning" in search_term
        assert '"John Doe"[Author]' in search_term
        assert '"Nature"[Journal]' in search_term
        assert " AND " in search_term
    
    def test_parse_single_article(self):
        """Test parsing a single PubMed article"""
        # Mock XML element
        xml_content = '''
        <PubmedArticle>
            <MedlineCitation>
                <PMID>12345678</PMID>
                <Article>
                    <ArticleTitle>Test Article Title</ArticleTitle>
                    <AuthorList>
                        <Author>
                            <LastName>Doe</LastName>
                            <ForeName>John</ForeName>
                        </Author>
                        <Author>
                            <LastName>Smith</LastName>
                            <ForeName>Jane</ForeName>
                        </Author>
                    </AuthorList>
                    <Journal>
                        <Title>Test Journal</Title>
                    </Journal>
                    <Abstract>
                        <AbstractText>Test abstract content</AbstractText>
                    </Abstract>
                </Article>
                <KeywordList>
                    <Keyword>test</Keyword>
                    <Keyword>research</Keyword>
                </KeywordList>
            </MedlineCitation>
            <PubmedData>
                <ArticleIdList>
                    <ArticleId IdType="doi">10.1000/test</ArticleId>
                </ArticleIdList>
            </PubmedData>
        </PubmedArticle>
        '''
        
        import xml.etree.ElementTree as ET
        article_elem = ET.fromstring(xml_content)
        
        result = self.pubmed._parse_single_article(article_elem)
        
        assert result is not None
        assert result.title == "Test Article Title"
        assert "John Doe" in result.authors
        assert "Jane Smith" in result.authors
        assert result.journal == "Test Journal"
        assert result.abstract == "Test abstract content"
        assert result.doi == "10.1000/test"
        assert "test" in result.keywords
        assert "research" in result.keywords
        assert result.database == "pubmed"
        assert result.database_id == "12345678"
    
    @patch('aiohttp.ClientSession.get')
    async def test_search_success(self, mock_get):
        """Test successful PubMed search"""
        # Mock search response
        search_response = Mock()
        search_response.status = 200
        search_response.json = AsyncMock(return_value={
            'esearchresult': {
                'idlist': ['12345678', '87654321']
            }
        })
        
        # Mock fetch response
        fetch_response = Mock()
        fetch_response.status = 200
        fetch_response.text = AsyncMock(return_value='''
        <PubmedArticleSet>
            <PubmedArticle>
                <MedlineCitation>
                    <PMID>12345678</PMID>
                    <Article>
                        <ArticleTitle>Test Article</ArticleTitle>
                        <AuthorList>
                            <Author>
                                <LastName>Doe</LastName>
                                <ForeName>John</ForeName>
                            </Author>
                        </AuthorList>
                    </Article>
                </MedlineCitation>
            </PubmedArticle>
        </PubmedArticleSet>
        ''')
        
        mock_get.return_value.__aenter__.side_effect = [search_response, fetch_response]
        
        query = SearchQuery(query="test query")
        results = await self.pubmed.search(query)
        
        assert len(results) == 1
        assert results[0].title == "Test Article"
        assert results[0].authors == ["John Doe"]

class TestArXivConnector:
    """Test arXiv integration"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.arxiv = ArXivConnector()
    
    def test_build_search_query(self):
        """Test building arXiv search queries"""
        query = SearchQuery(
            query="machine learning",
            author="John Doe"
        )
        
        search_query = self.arxiv._build_search_query(query)
        
        assert "all:machine learning" in search_query
        assert "au:John Doe" in search_query
        assert " AND " in search_query
    
    def test_map_sort_order(self):
        """Test mapping sort orders"""
        assert self.arxiv._map_sort_order("relevance") == "relevance"
        assert self.arxiv._map_sort_order("date") == "submittedDate"
        assert self.arxiv._map_sort_order("citations") == "relevance"
        assert self.arxiv._map_sort_order("unknown") == "relevance"
    
    def test_parse_arxiv_entry(self):
        """Test parsing arXiv entry"""
        xml_content = '''
        <entry>
            <id>http://arxiv.org/abs/2301.12345v1</id>
            <title>Test arXiv Paper</title>
            <author>
                <name>John Doe</name>
            </author>
            <author>
                <name>Jane Smith</name>
            </author>
            <summary>This is a test abstract for an arXiv paper.</summary>
            <published>2023-01-15T00:00:00Z</published>
            <link href="http://arxiv.org/pdf/2301.12345v1.pdf" type="application/pdf"/>
            <category term="cs.AI"/>
            <category term="cs.LG"/>
        </entry>
        '''
        
        import xml.etree.ElementTree as ET
        entry_elem = ET.fromstring(xml_content)
        
        result = self.arxiv._parse_arxiv_entry(entry_elem)
        
        assert result is not None
        assert result.title == "Test arXiv Paper"
        assert "John Doe" in result.authors
        assert "Jane Smith" in result.authors
        assert result.abstract == "This is a test abstract for an arXiv paper."
        assert result.year == 2023
        assert result.database == "arxiv"
        assert result.database_id == "2301.12345v1"
        assert result.pdf_url == "http://arxiv.org/pdf/2301.12345v1.pdf"
        assert "cs.AI" in result.keywords
        assert "cs.LG" in result.keywords

class TestGoogleScholarConnector:
    """Test Google Scholar integration"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.scholar = GoogleScholarConnector()
    
    def test_build_search_query(self):
        """Test building Google Scholar search queries"""
        query = SearchQuery(
            query="machine learning",
            author="John Doe"
        )
        
        search_query = self.scholar._build_search_query(query)
        
        assert "machine learning" in search_query
        assert 'author:"John Doe"' in search_query
    
    def test_parse_scholar_article(self):
        """Test parsing Google Scholar article (simplified)"""
        # Mock HTML content
        article_html = '''
        <div class="gs_r gs_or gs_scl">
            <h3><a href="https://example.com/paper">Test Paper Title</a></h3>
            <div class="gs_a">J Doe, J Smith - Test Journal, 2023 - example.com</div>
            <div class="gs_fl">
                <a href="#">Cited by 42</a>
            </div>
        </div>
        '''
        
        result = self.scholar._parse_scholar_article(article_html)
        
        assert result is not None
        assert result.title == "Test Paper Title"
        assert result.url == "https://example.com/paper"
        assert result.year == 2023
        assert result.citation_count == 42
        assert result.database == "google_scholar"

class TestAcademicDatabaseService:
    """Test unified academic database service"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.service = AcademicDatabaseService()
    
    def test_get_supported_databases(self):
        """Test getting supported databases"""
        databases = self.service.get_supported_databases()
        
        assert "pubmed" in databases
        assert "arxiv" in databases
        assert "google_scholar" in databases
        assert len(databases) == 3
    
    def test_validate_query_valid(self):
        """Test query validation with valid query"""
        query = SearchQuery(
            query="machine learning",
            max_results=20,
            start_date=datetime(2020, 1, 1),
            end_date=datetime(2023, 12, 31)
        )
        
        assert self.service.validate_query(query) is True
    
    def test_validate_query_invalid_empty(self):
        """Test query validation with empty query"""
        query = SearchQuery(query="")
        assert self.service.validate_query(query) is False
        
        query = SearchQuery(query="   ")
        assert self.service.validate_query(query) is False
    
    def test_validate_query_invalid_results(self):
        """Test query validation with invalid max_results"""
        query = SearchQuery(query="test", max_results=0)
        assert self.service.validate_query(query) is False
        
        query = SearchQuery(query="test", max_results=2000)
        assert self.service.validate_query(query) is False
    
    def test_validate_query_invalid_dates(self):
        """Test query validation with invalid date range"""
        query = SearchQuery(
            query="test",
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2022, 1, 1)  # End before start
        )
        
        assert self.service.validate_query(query) is False
    
    async def test_search_database_invalid_type(self):
        """Test error handling for invalid database type"""
        query = SearchQuery(query="test")
        
        with pytest.raises(ValueError):
            # This should raise ValueError for invalid enum
            invalid_db = DatabaseType("invalid_db")
    
    @patch.object(PubMedConnector, 'search')
    async def test_search_database_success(self, mock_search):
        """Test successful database search"""
        mock_results = [
            SearchResult(
                title="Test Article",
                authors=["John Doe"],
                database="pubmed"
            )
        ]
        mock_search.return_value = mock_results
        
        query = SearchQuery(query="test")
        results = await self.service.search_database(DatabaseType.PUBMED, query)
        
        assert len(results) == 1
        assert results[0].title == "Test Article"
        mock_search.assert_called_once_with(query)
    
    def test_deduplicate_results(self):
        """Test result deduplication"""
        results = [
            SearchResult(title="Test Article", authors=[], database="pubmed"),
            SearchResult(title="Test Article!", authors=[], database="arxiv"),  # Similar title
            SearchResult(title="Different Article", authors=[], database="pubmed"),
            SearchResult(title="Test Article.", authors=[], database="scholar")  # Similar title
        ]
        
        deduplicated = self.service._deduplicate_results(results)
        
        # Should keep only 2 unique titles
        assert len(deduplicated) == 2
        titles = [result.title for result in deduplicated]
        assert "Test Article" in titles
        assert "Different Article" in titles
    
    @patch.object(PubMedConnector, 'search')
    @patch.object(ArXivConnector, 'search')
    async def test_unified_search(self, mock_arxiv_search, mock_pubmed_search):
        """Test unified search across databases"""
        mock_pubmed_search.return_value = [
            SearchResult(title="PubMed Article", authors=[], database="pubmed")
        ]
        mock_arxiv_search.return_value = [
            SearchResult(title="arXiv Article", authors=[], database="arxiv")
        ]
        
        query = SearchQuery(query="test")
        results = await self.service.unified_search(query, [DatabaseType.PUBMED, DatabaseType.ARXIV])
        
        assert len(results) == 2
        titles = [result.title for result in results]
        assert "PubMed Article" in titles
        assert "arXiv Article" in titles

if __name__ == "__main__":
    pytest.main([__file__])