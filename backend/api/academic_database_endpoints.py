"""
Academic Database API Endpoints

Provides REST API endpoints for academic database integrations:
- PubMed search and metadata extraction
- arXiv paper discovery and access
- Google Scholar search with rate limiting
- Unified search across multiple databases
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from ..services.academic_database_service import (
    AcademicDatabaseService,
    DatabaseType,
    SearchQuery,
    SearchResult
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/academic-databases", tags=["academic-databases"])

# Pydantic models for API
class SearchQueryRequest(BaseModel):
    query: str = Field(..., description="Search query string")
    max_results: int = Field(20, ge=1, le=100, description="Maximum number of results")
    start_date: Optional[datetime] = Field(None, description="Start date filter")
    end_date: Optional[datetime] = Field(None, description="End date filter")
    journal: Optional[str] = Field(None, description="Journal name filter")
    author: Optional[str] = Field(None, description="Author name filter")
    sort_by: str = Field("relevance", description="Sort order: relevance, date, citations")

class SearchResultResponse(BaseModel):
    title: str
    authors: List[str]
    abstract: Optional[str] = None
    journal: Optional[str] = None
    year: Optional[int] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    pdf_url: Optional[str] = None
    citation_count: Optional[int] = None
    database: str
    database_id: Optional[str] = None
    keywords: List[str] = []
    publication_date: Optional[datetime] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    publisher: Optional[str] = None

class DatabaseSearchResponse(BaseModel):
    success: bool
    database: str
    total_results: int
    results: List[SearchResultResponse]
    query_time_ms: int
    errors: List[str] = []

class UnifiedSearchResponse(BaseModel):
    success: bool
    total_results: int
    results_by_database: Dict[str, int]
    results: List[SearchResultResponse]
    query_time_ms: int
    errors: List[str] = []

# Initialize service
academic_db_service = AcademicDatabaseService()

@router.get("/supported")
async def get_supported_databases():
    """Get list of supported academic databases"""
    try:
        databases = academic_db_service.get_supported_databases()
        return {
            "success": True,
            "databases": databases,
            "descriptions": {
                "pubmed": "PubMed - Biomedical literature database",
                "arxiv": "arXiv - Preprint repository for physics, mathematics, computer science",
                "google_scholar": "Google Scholar - Academic search engine (rate limited)"
            },
            "features": {
                "pubmed": ["advanced_search", "metadata_extraction", "api_access"],
                "arxiv": ["full_text_access", "pdf_download", "category_filtering"],
                "google_scholar": ["citation_counts", "broad_coverage", "web_scraping"]
            }
        }
    except Exception as e:
        logger.error(f"Error getting supported databases: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search/{database}", response_model=DatabaseSearchResponse)
async def search_database(
    database: str,
    request: SearchQueryRequest
):
    """Search a specific academic database"""
    try:
        # Validate database type
        try:
            db_type = DatabaseType(database.lower())
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported database: {database}. Supported: {academic_db_service.get_supported_databases()}"
            )
        
        # Create search query
        search_query = SearchQuery(
            query=request.query,
            max_results=request.max_results,
            start_date=request.start_date,
            end_date=request.end_date,
            journal=request.journal,
            author=request.author,
            sort_by=request.sort_by
        )
        
        # Validate query
        if not academic_db_service.validate_query(search_query):
            raise HTTPException(status_code=400, detail="Invalid search query parameters")
        
        # Perform search
        start_time = datetime.now()
        results = await academic_db_service.search_database(db_type, search_query)
        end_time = datetime.now()
        
        query_time_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Convert results to response format
        result_responses = [
            SearchResultResponse(
                title=result.title,
                authors=result.authors,
                abstract=result.abstract,
                journal=result.journal,
                year=result.year,
                doi=result.doi,
                url=result.url,
                pdf_url=result.pdf_url,
                citation_count=result.citation_count,
                database=result.database,
                database_id=result.database_id,
                keywords=result.keywords or [],
                publication_date=result.publication_date,
                volume=result.volume,
                issue=result.issue,
                pages=result.pages,
                publisher=result.publisher
            )
            for result in results
        ]
        
        return DatabaseSearchResponse(
            success=True,
            database=database,
            total_results=len(result_responses),
            results=result_responses,
            query_time_ms=query_time_ms
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching {database}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search/unified", response_model=UnifiedSearchResponse)
async def unified_search(
    request: SearchQueryRequest,
    databases: Optional[List[str]] = Query(None, description="Specific databases to search")
):
    """Search across multiple academic databases"""
    try:
        # Parse database types
        db_types = None
        if databases:
            try:
                db_types = [DatabaseType(db.lower()) for db in databases]
            except ValueError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid database specified: {e}"
                )
        
        # Create search query
        search_query = SearchQuery(
            query=request.query,
            max_results=request.max_results,
            start_date=request.start_date,
            end_date=request.end_date,
            journal=request.journal,
            author=request.author,
            sort_by=request.sort_by
        )
        
        # Validate query
        if not academic_db_service.validate_query(search_query):
            raise HTTPException(status_code=400, detail="Invalid search query parameters")
        
        # Perform unified search
        start_time = datetime.now()
        results = await academic_db_service.unified_search(search_query, db_types)
        end_time = datetime.now()
        
        query_time_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Count results by database
        results_by_database = {}
        for result in results:
            db_name = result.database
            results_by_database[db_name] = results_by_database.get(db_name, 0) + 1
        
        # Convert results to response format
        result_responses = [
            SearchResultResponse(
                title=result.title,
                authors=result.authors,
                abstract=result.abstract,
                journal=result.journal,
                year=result.year,
                doi=result.doi,
                url=result.url,
                pdf_url=result.pdf_url,
                citation_count=result.citation_count,
                database=result.database,
                database_id=result.database_id,
                keywords=result.keywords or [],
                publication_date=result.publication_date,
                volume=result.volume,
                issue=result.issue,
                pages=result.pages,
                publisher=result.publisher
            )
            for result in results
        ]
        
        return UnifiedSearchResponse(
            success=True,
            total_results=len(result_responses),
            results_by_database=results_by_database,
            results=result_responses,
            query_time_ms=query_time_ms
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in unified search: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search/all", response_model=Dict[str, DatabaseSearchResponse])
async def search_all_databases(request: SearchQueryRequest):
    """Search all supported databases concurrently"""
    try:
        # Create search query
        search_query = SearchQuery(
            query=request.query,
            max_results=request.max_results,
            start_date=request.start_date,
            end_date=request.end_date,
            journal=request.journal,
            author=request.author,
            sort_by=request.sort_by
        )
        
        # Validate query
        if not academic_db_service.validate_query(search_query):
            raise HTTPException(status_code=400, detail="Invalid search query parameters")
        
        # Perform search across all databases
        start_time = datetime.now()
        all_results = await academic_db_service.search_all_databases(search_query)
        end_time = datetime.now()
        
        query_time_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Format response for each database
        response = {}
        for db_name, results in all_results.items():
            result_responses = [
                SearchResultResponse(
                    title=result.title,
                    authors=result.authors,
                    abstract=result.abstract,
                    journal=result.journal,
                    year=result.year,
                    doi=result.doi,
                    url=result.url,
                    pdf_url=result.pdf_url,
                    citation_count=result.citation_count,
                    database=result.database,
                    database_id=result.database_id,
                    keywords=result.keywords or [],
                    publication_date=result.publication_date,
                    volume=result.volume,
                    issue=result.issue,
                    pages=result.pages,
                    publisher=result.publisher
                )
                for result in results
            ]
            
            response[db_name] = DatabaseSearchResponse(
                success=True,
                database=db_name,
                total_results=len(result_responses),
                results=result_responses,
                query_time_ms=query_time_ms
            )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching all databases: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/paper/{database}/{paper_id}")
async def get_paper_details(database: str, paper_id: str):
    """Get detailed information for a specific paper"""
    try:
        # Validate database type
        try:
            db_type = DatabaseType(database.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported database: {database}"
            )
        
        # Get paper details
        result = await academic_db_service.get_paper_details(db_type, paper_id)
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Paper not found: {paper_id} in {database}"
            )
        
        return SearchResultResponse(
            title=result.title,
            authors=result.authors,
            abstract=result.abstract,
            journal=result.journal,
            year=result.year,
            doi=result.doi,
            url=result.url,
            pdf_url=result.pdf_url,
            citation_count=result.citation_count,
            database=result.database,
            database_id=result.database_id,
            keywords=result.keywords or [],
            publication_date=result.publication_date,
            volume=result.volume,
            issue=result.issue,
            pages=result.pages,
            publisher=result.publisher
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting paper details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "academic_databases",
        "timestamp": datetime.now().isoformat(),
        "supported_databases": academic_db_service.get_supported_databases()
    }

@router.get("/stats")
async def get_database_stats():
    """Get database integration statistics"""
    try:
        return {
            "supported_databases": academic_db_service.get_supported_databases(),
            "total_databases": len(academic_db_service.get_supported_databases()),
            "api_based": ["pubmed", "arxiv"],
            "web_scraping": ["google_scholar"],
            "rate_limits": {
                "pubmed": "3 requests/second",
                "arxiv": "1 request/3 seconds", 
                "google_scholar": "1 request/10 seconds"
            },
            "features": {
                "unified_search": True,
                "concurrent_search": True,
                "deduplication": True,
                "metadata_extraction": True
            }
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))