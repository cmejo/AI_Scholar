"""
Academic Database Integration Service

This service provides integration with major academic databases:
- PubMed (via Entrez API)
- arXiv (via arXiv API)
- Google Scholar (via web scraping with rate limiting)

Supports advanced search, metadata extraction, and unified interface.
"""

import asyncio
import json
import logging
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import xml.etree.ElementTree as ET
from urllib.parse import urlencode, quote_plus
import random

logger = logging.getLogger(__name__)

class DatabaseType(Enum):
    PUBMED = "pubmed"
    ARXIV = "arxiv"
    GOOGLE_SCHOLAR = "google_scholar"

@dataclass
class SearchResult:
    """Unified search result structure"""
    title: str
    authors: List[str]
    abstract: Optional[str] = None
    journal: Optional[str] = None
    year: Optional[int] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    pdf_url: Optional[str] = None
    citation_count: Optional[int] = None
    database: str = ""
    database_id: Optional[str] = None
    keywords: List[str] = None
    publication_date: Optional[datetime] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    publisher: Optional[str] = None
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []

@dataclass
class SearchQuery:
    """Search query parameters"""
    query: str
    max_results: int = 20
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    journal: Optional[str] = None
    author: Optional[str] = None
    sort_by: str = "relevance"  # relevance, date, citations
    
class RateLimiter:
    """Rate limiter for API requests"""
    
    def __init__(self, max_requests: int, time_window: int):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
    
    async def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        now = time.time()
        
        # Remove old requests outside time window
        self.requests = [req_time for req_time in self.requests 
                        if now - req_time < self.time_window]
        
        # Check if we need to wait
        if len(self.requests) >= self.max_requests:
            sleep_time = self.time_window - (now - self.requests[0]) + 1
            if sleep_time > 0:
                logger.info(f"Rate limit reached, waiting {sleep_time:.1f} seconds")
                await asyncio.sleep(sleep_time)
        
        # Record this request
        self.requests.append(now)

class PubMedConnector:
    """PubMed/NCBI Entrez API integration"""
    
    def __init__(self, email: str = "user@example.com", api_key: Optional[str] = None):
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        self.email = email
        self.api_key = api_key
        self.rate_limiter = RateLimiter(max_requests=3, time_window=1)  # 3 requests per second
        
    async def search(self, query: SearchQuery) -> List[SearchResult]:
        """Search PubMed database"""
        try:
            # First, search for article IDs
            search_params = {
                'db': 'pubmed',
                'term': self._build_search_term(query),
                'retmax': query.max_results,
                'retmode': 'json',
                'tool': 'ai_scholar',
                'email': self.email
            }
            
            if self.api_key:
                search_params['api_key'] = self.api_key
            
            await self.rate_limiter.wait_if_needed()
            
            async with aiohttp.ClientSession() as session:
                # Search for IDs
                search_url = f"{self.base_url}/esearch.fcgi"
                async with session.get(search_url, params=search_params) as response:
                    if response.status != 200:
                        raise Exception(f"PubMed search failed: {response.status}")
                    
                    search_data = await response.json()
                    id_list = search_data.get('esearchresult', {}).get('idlist', [])
                    
                    if not id_list:
                        return []
                    
                    # Fetch detailed information for each ID
                    return await self._fetch_details(session, id_list)
                    
        except Exception as e:
            logger.error(f"PubMed search error: {e}")
            return []
    
    async def _fetch_details(self, session: aiohttp.ClientSession, 
                           id_list: List[str]) -> List[SearchResult]:
        """Fetch detailed information for PubMed articles"""
        results = []
        
        # Process IDs in batches to avoid URL length limits
        batch_size = 200
        for i in range(0, len(id_list), batch_size):
            batch_ids = id_list[i:i + batch_size]
            
            fetch_params = {
                'db': 'pubmed',
                'id': ','.join(batch_ids),
                'retmode': 'xml',
                'tool': 'ai_scholar',
                'email': self.email
            }
            
            if self.api_key:
                fetch_params['api_key'] = self.api_key
            
            await self.rate_limiter.wait_if_needed()
            
            fetch_url = f"{self.base_url}/efetch.fcgi"
            async with session.get(fetch_url, params=fetch_params) as response:
                if response.status == 200:
                    xml_data = await response.text()
                    batch_results = self._parse_pubmed_xml(xml_data)
                    results.extend(batch_results)
        
        return results
    
    def _build_search_term(self, query: SearchQuery) -> str:
        """Build PubMed search term"""
        terms = [query.query]
        
        if query.author:
            terms.append(f'"{query.author}"[Author]')
        
        if query.journal:
            terms.append(f'"{query.journal}"[Journal]')
        
        if query.start_date:
            date_str = query.start_date.strftime('%Y/%m/%d')
            terms.append(f'"{date_str}"[Date - Publication] : "3000"[Date - Publication]')
        
        return ' AND '.join(terms)
    
    def _parse_pubmed_xml(self, xml_data: str) -> List[SearchResult]:
        """Parse PubMed XML response"""
        results = []
        
        try:
            root = ET.fromstring(xml_data)
            
            for article in root.findall('.//PubmedArticle'):
                try:
                    result = self._parse_single_article(article)
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.warning(f"Error parsing PubMed article: {e}")
                    continue
                    
        except ET.ParseError as e:
            logger.error(f"XML parsing error: {e}")
        
        return results
    
    def _parse_single_article(self, article: ET.Element) -> Optional[SearchResult]:
        """Parse a single PubMed article"""
        try:
            # Extract basic information
            medline_citation = article.find('.//MedlineCitation')
            if medline_citation is None:
                return None
            
            pmid = medline_citation.find('.//PMID')
            pmid_text = pmid.text if pmid is not None else None
            
            # Title
            title_elem = article.find('.//ArticleTitle')
            title = title_elem.text if title_elem is not None else ""
            
            # Authors
            authors = []
            author_list = article.find('.//AuthorList')
            if author_list is not None:
                for author in author_list.findall('.//Author'):
                    last_name = author.find('.//LastName')
                    first_name = author.find('.//ForeName')
                    if last_name is not None:
                        name = last_name.text
                        if first_name is not None:
                            name = f"{first_name.text} {name}"
                        authors.append(name)
            
            # Abstract
            abstract_elem = article.find('.//Abstract/AbstractText')
            abstract = abstract_elem.text if abstract_elem is not None else None
            
            # Journal
            journal_elem = article.find('.//Journal/Title')
            journal = journal_elem.text if journal_elem is not None else None
            
            # Publication date
            pub_date = article.find('.//PubDate')
            year = None
            pub_datetime = None
            if pub_date is not None:
                year_elem = pub_date.find('.//Year')
                if year_elem is not None:
                    try:
                        year = int(year_elem.text)
                        pub_datetime = datetime(year, 1, 1)
                    except ValueError:
                        pass
            
            # DOI
            doi = None
            article_ids = article.findall('.//ArticleId')
            for article_id in article_ids:
                if article_id.get('IdType') == 'doi':
                    doi = article_id.text
                    break
            
            # Keywords
            keywords = []
            keyword_list = article.find('.//KeywordList')
            if keyword_list is not None:
                for keyword in keyword_list.findall('.//Keyword'):
                    if keyword.text:
                        keywords.append(keyword.text)
            
            # Volume, Issue, Pages
            volume_elem = article.find('.//Volume')
            volume = volume_elem.text if volume_elem is not None else None
            
            issue_elem = article.find('.//Issue')
            issue = issue_elem.text if issue_elem is not None else None
            
            pages_elem = article.find('.//MedlinePgn')
            pages = pages_elem.text if pages_elem is not None else None
            
            return SearchResult(
                title=title,
                authors=authors,
                abstract=abstract,
                journal=journal,
                year=year,
                doi=doi,
                url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid_text}/" if pmid_text else None,
                database="pubmed",
                database_id=pmid_text,
                keywords=keywords,
                publication_date=pub_datetime,
                volume=volume,
                issue=issue,
                pages=pages
            )
            
        except Exception as e:
            logger.error(f"Error parsing PubMed article: {e}")
            return None

class ArXivConnector:
    """arXiv API integration"""
    
    def __init__(self):
        self.base_url = "http://export.arxiv.org/api/query"
        self.rate_limiter = RateLimiter(max_requests=1, time_window=3)  # 1 request per 3 seconds
    
    async def search(self, query: SearchQuery) -> List[SearchResult]:
        """Search arXiv database"""
        try:
            search_params = {
                'search_query': self._build_search_query(query),
                'start': 0,
                'max_results': query.max_results,
                'sortBy': self._map_sort_order(query.sort_by),
                'sortOrder': 'descending'
            }
            
            await self.rate_limiter.wait_if_needed()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=search_params) as response:
                    if response.status != 200:
                        raise Exception(f"arXiv search failed: {response.status}")
                    
                    xml_data = await response.text()
                    return self._parse_arxiv_xml(xml_data)
                    
        except Exception as e:
            logger.error(f"arXiv search error: {e}")
            return []
    
    def _build_search_query(self, query: SearchQuery) -> str:
        """Build arXiv search query"""
        # arXiv uses a different query format
        search_terms = []
        
        # Main query in title and abstract
        if query.query:
            search_terms.append(f'all:{query.query}')
        
        if query.author:
            search_terms.append(f'au:{query.author}')
        
        return ' AND '.join(search_terms) if search_terms else query.query
    
    def _map_sort_order(self, sort_by: str) -> str:
        """Map sort order to arXiv format"""
        mapping = {
            'relevance': 'relevance',
            'date': 'submittedDate',
            'citations': 'relevance'  # arXiv doesn't have citation sorting
        }
        return mapping.get(sort_by, 'relevance')
    
    def _parse_arxiv_xml(self, xml_data: str) -> List[SearchResult]:
        """Parse arXiv XML response"""
        results = []
        
        try:
            # Remove namespace for easier parsing
            xml_data = xml_data.replace('xmlns="http://www.w3.org/2005/Atom"', '')
            root = ET.fromstring(xml_data)
            
            for entry in root.findall('.//entry'):
                try:
                    result = self._parse_arxiv_entry(entry)
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.warning(f"Error parsing arXiv entry: {e}")
                    continue
                    
        except ET.ParseError as e:
            logger.error(f"XML parsing error: {e}")
        
        return results
    
    def _parse_arxiv_entry(self, entry: ET.Element) -> Optional[SearchResult]:
        """Parse a single arXiv entry"""
        try:
            # Title
            title_elem = entry.find('.//title')
            title = title_elem.text.strip() if title_elem is not None else ""
            
            # Authors
            authors = []
            for author in entry.findall('.//author'):
                name_elem = author.find('.//name')
                if name_elem is not None:
                    authors.append(name_elem.text.strip())
            
            # Abstract
            summary_elem = entry.find('.//summary')
            abstract = summary_elem.text.strip() if summary_elem is not None else None
            
            # arXiv ID and URL
            id_elem = entry.find('.//id')
            arxiv_url = id_elem.text if id_elem is not None else None
            arxiv_id = None
            if arxiv_url:
                arxiv_id = arxiv_url.split('/')[-1]
            
            # PDF URL
            pdf_url = None
            for link in entry.findall('.//link'):
                if link.get('type') == 'application/pdf':
                    pdf_url = link.get('href')
                    break
            
            # Publication date
            published_elem = entry.find('.//published')
            pub_datetime = None
            year = None
            if published_elem is not None:
                try:
                    pub_datetime = datetime.fromisoformat(published_elem.text.replace('Z', '+00:00'))
                    year = pub_datetime.year
                except ValueError:
                    pass
            
            # Categories (as keywords)
            keywords = []
            for category in entry.findall('.//category'):
                term = category.get('term')
                if term:
                    keywords.append(term)
            
            # DOI (if available)
            doi = None
            doi_elem = entry.find('.//arxiv:doi', {'arxiv': 'http://arxiv.org/schemas/atom'})
            if doi_elem is not None:
                doi = doi_elem.text
            
            return SearchResult(
                title=title,
                authors=authors,
                abstract=abstract,
                year=year,
                doi=doi,
                url=arxiv_url,
                pdf_url=pdf_url,
                database="arxiv",
                database_id=arxiv_id,
                keywords=keywords,
                publication_date=pub_datetime,
                journal="arXiv preprint"
            )
            
        except Exception as e:
            logger.error(f"Error parsing arXiv entry: {e}")
            return None

class GoogleScholarConnector:
    """Google Scholar integration via web scraping"""
    
    def __init__(self):
        self.base_url = "https://scholar.google.com/scholar"
        self.rate_limiter = RateLimiter(max_requests=1, time_window=10)  # Very conservative rate limiting
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
    
    async def search(self, query: SearchQuery) -> List[SearchResult]:
        """Search Google Scholar (with rate limiting and respectful scraping)"""
        try:
            search_params = {
                'q': self._build_search_query(query),
                'num': min(query.max_results, 20),  # Limit to 20 results max
                'hl': 'en'
            }
            
            if query.start_date:
                search_params['as_ylo'] = query.start_date.year
            if query.end_date:
                search_params['as_yhi'] = query.end_date.year
            
            await self.rate_limiter.wait_if_needed()
            
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=search_params, headers=headers) as response:
                    if response.status == 429:
                        logger.warning("Google Scholar rate limit hit, waiting longer")
                        await asyncio.sleep(60)  # Wait 1 minute if rate limited
                        return []
                    elif response.status != 200:
                        raise Exception(f"Google Scholar search failed: {response.status}")
                    
                    html_content = await response.text()
                    return self._parse_scholar_html(html_content)
                    
        except Exception as e:
            logger.error(f"Google Scholar search error: {e}")
            return []
    
    def _build_search_query(self, query: SearchQuery) -> str:
        """Build Google Scholar search query"""
        search_terms = [query.query]
        
        if query.author:
            search_terms.append(f'author:"{query.author}"')
        
        return ' '.join(search_terms)
    
    def _parse_scholar_html(self, html_content: str) -> List[SearchResult]:
        """Parse Google Scholar HTML response"""
        results = []
        
        try:
            # This is a simplified parser - in production, you'd want to use BeautifulSoup
            # For now, we'll extract basic information using regex
            
            # Extract article blocks
            article_pattern = r'<div class="gs_r gs_or gs_scl".*?</div></div></div>'
            articles = re.findall(article_pattern, html_content, re.DOTALL)
            
            for article_html in articles:
                try:
                    result = self._parse_scholar_article(article_html)
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.warning(f"Error parsing Scholar article: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"HTML parsing error: {e}")
        
        return results
    
    def _parse_scholar_article(self, article_html: str) -> Optional[SearchResult]:
        """Parse a single Google Scholar article (simplified)"""
        try:
            # Extract title
            title_match = re.search(r'<h3[^>]*><a[^>]*>([^<]+)</a></h3>', article_html)
            title = title_match.group(1) if title_match else ""
            
            # Extract URL
            url_match = re.search(r'<h3[^>]*><a href="([^"]+)"', article_html)
            url = url_match.group(1) if url_match else None
            
            # Extract authors and publication info
            authors = []
            year = None
            journal = None
            
            # This is a very basic extraction - would need more sophisticated parsing
            author_pattern = r'<div class="gs_a">([^<]+)</div>'
            author_match = re.search(author_pattern, article_html)
            if author_match:
                author_info = author_match.group(1)
                # Try to extract year
                year_match = re.search(r'\b(19|20)\d{2}\b', author_info)
                if year_match:
                    year = int(year_match.group())
                
                # Extract authors (simplified)
                author_parts = author_info.split(' - ')
                if author_parts:
                    author_text = author_parts[0]
                    authors = [name.strip() for name in author_text.split(',')]
            
            # Extract citation count
            citation_count = None
            citation_match = re.search(r'Cited by (\d+)', article_html)
            if citation_match:
                citation_count = int(citation_match.group(1))
            
            return SearchResult(
                title=title,
                authors=authors,
                year=year,
                url=url,
                citation_count=citation_count,
                database="google_scholar",
                journal=journal
            )
            
        except Exception as e:
            logger.error(f"Error parsing Scholar article: {e}")
            return None

class AcademicDatabaseService:
    """Unified academic database service"""
    
    def __init__(self, pubmed_email: str = "user@example.com", 
                 pubmed_api_key: Optional[str] = None):
        self.pubmed = PubMedConnector(pubmed_email, pubmed_api_key)
        self.arxiv = ArXivConnector()
        self.scholar = GoogleScholarConnector()
        
        self.connectors = {
            DatabaseType.PUBMED: self.pubmed,
            DatabaseType.ARXIV: self.arxiv,
            DatabaseType.GOOGLE_SCHOLAR: self.scholar
        }
    
    async def search_database(self, database: DatabaseType, 
                            query: SearchQuery) -> List[SearchResult]:
        """Search a specific database"""
        try:
            connector = self.connectors.get(database)
            if not connector:
                raise ValueError(f"Unsupported database: {database}")
            
            return await connector.search(query)
            
        except Exception as e:
            logger.error(f"Database search error for {database}: {e}")
            return []
    
    async def search_all_databases(self, query: SearchQuery) -> Dict[str, List[SearchResult]]:
        """Search all databases concurrently"""
        tasks = []
        
        for db_type in DatabaseType:
            task = asyncio.create_task(
                self.search_database(db_type, query),
                name=f"search_{db_type.value}"
            )
            tasks.append((db_type.value, task))
        
        results = {}
        for db_name, task in tasks:
            try:
                results[db_name] = await task
            except Exception as e:
                logger.error(f"Error searching {db_name}: {e}")
                results[db_name] = []
        
        return results
    
    async def unified_search(self, query: SearchQuery, 
                           databases: Optional[List[DatabaseType]] = None) -> List[SearchResult]:
        """Perform unified search across specified databases"""
        if databases is None:
            databases = list(DatabaseType)
        
        all_results = []
        
        for db_type in databases:
            try:
                results = await self.search_database(db_type, query)
                all_results.extend(results)
            except Exception as e:
                logger.error(f"Error in unified search for {db_type}: {e}")
        
        # Remove duplicates based on title similarity
        return self._deduplicate_results(all_results)
    
    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Remove duplicate results based on title similarity"""
        if not results:
            return results
        
        unique_results = []
        seen_titles = set()
        
        for result in results:
            # Normalize title for comparison
            normalized_title = re.sub(r'[^\w\s]', '', result.title.lower()).strip()
            
            if normalized_title not in seen_titles:
                seen_titles.add(normalized_title)
                unique_results.append(result)
        
        return unique_results
    
    def get_supported_databases(self) -> List[str]:
        """Get list of supported databases"""
        return [db.value for db in DatabaseType]
    
    async def get_paper_details(self, database: DatabaseType, 
                              paper_id: str) -> Optional[SearchResult]:
        """Get detailed information for a specific paper"""
        # This would be implemented to fetch detailed info by ID
        # For now, return None as placeholder
        logger.warning("get_paper_details not yet implemented")
        return None
    
    def validate_query(self, query: SearchQuery) -> bool:
        """Validate search query parameters"""
        if not query.query or not query.query.strip():
            return False
        
        if query.max_results <= 0 or query.max_results > 1000:
            return False
        
        if query.start_date and query.end_date:
            if query.start_date > query.end_date:
                return False
        
        return True