"""
Basic test for academic database service
"""

import asyncio
from services.academic_database_service import (
    AcademicDatabaseService,
    SearchQuery,
    SearchResult,
    DatabaseType
)

def test_basic_functionality():
    """Test basic service functionality"""
    service = AcademicDatabaseService()
    
    # Test getting supported databases
    databases = service.get_supported_databases()
    print(f"Supported databases: {databases}")
    assert "pubmed" in databases
    assert "arxiv" in databases
    assert "google_scholar" in databases
    
    # Test creating search query
    query = SearchQuery(
        query="machine learning",
        max_results=10,
        author="John Doe"
    )
    
    print(f"Created search query: {query.query}")
    assert query.query == "machine learning"
    assert query.max_results == 10
    assert query.author == "John Doe"
    
    # Test query validation
    valid_query = SearchQuery(query="test query")
    invalid_query = SearchQuery(query="")
    
    assert service.validate_query(valid_query) is True
    assert service.validate_query(invalid_query) is False
    
    # Test creating search result
    result = SearchResult(
        title="Test Article",
        authors=["John Doe", "Jane Smith"],
        abstract="Test abstract",
        database="pubmed",
        year=2023
    )
    
    print(f"Created search result: {result.title}")
    assert result.title == "Test Article"
    assert len(result.authors) == 2
    assert result.database == "pubmed"
    
    print("All basic tests passed!")

if __name__ == "__main__":
    test_basic_functionality()