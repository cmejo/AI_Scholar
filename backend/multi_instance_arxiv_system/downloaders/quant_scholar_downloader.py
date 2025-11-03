"""
Quant Scholar Downloader for multi-instance ArXiv system.

Specialized downloader for Quant Scholar instance that handles:
- arXiv categories: econ.EM, econ.GN, econ.TH, eess.SY, math.ST, math.PR, math.OC, q-fin.*, stat.*
- Wildcard category matching (q-fin.*, stat.*)
- Journal sources: Journal of Statistical Software, R Journal
- Progress tracking and resume functionality
- Integration with existing RAG infrastructure
"""

import asyncio
import logging
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
import requests
import aiohttp
import aiofiles
from urllib.parse import urlencode
import json
import hashlib
import os
import re

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from ..base.base_scholar_downloader import (
    BaseScholarDownloader, DateRange, DownloadResult, ProcessingResult
)
from ..shared.multi_instance_data_models import (
    BasePaper, ArxivPaper, JournalPaper, InstanceConfig, UpdateReport
)
from ..processors.quant_scholar_processor import QuantScholarProcessor
from ..error_handling.quant_scholar_error_handler import (
    QuantScholarErrorHandler, ErrorCategory, ErrorSeverity
)

# Import existing services
try:
    from services.scientific_pdf_processor import ScientificPDFProcessor
    from services.vector_store_service import VectorStoreService
except ImportError as e:
    logging.warning(f"Could not import existing services: {e}")
    ScientificPDFProcessor = None
    VectorStoreService = None

logger = logging.getLogger(__name__)


class ArxivAPIClient:
    """Client for arXiv API to discover papers with wildcard support."""
    
    def __init__(self):
        self.base_url = "http://export.arxiv.org/api/query"
        self.rate_limit_delay = 3.0  # 3 seconds between requests as per arXiv guidelines
        self.last_request_time = 0  
      
    async def _rate_limit(self):
        """Enforce rate limiting between API requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            await asyncio.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _expand_wildcard_categories(self, categories: List[str]) -> List[str]:
        """
        Expand wildcard categories like 'q-fin.*' and 'stat.*' to actual categories.
        
        Args:
            categories: List of categories that may include wildcards
            
        Returns:
            List of expanded categories
        """
        expanded = []
        
        # Known arXiv categories for quantitative finance and statistics
        qfin_categories = [
            'q-fin.CP', 'q-fin.EC', 'q-fin.GN', 'q-fin.MF', 'q-fin.PM', 
            'q-fin.PR', 'q-fin.RM', 'q-fin.ST', 'q-fin.TR'
        ]
        
        stat_categories = [
            'stat.AP', 'stat.CO', 'stat.ME', 'stat.ML', 'stat.OT', 'stat.TH'
        ]
        
        for category in categories:
            if category == 'q-fin.*':
                expanded.extend(qfin_categories)
            elif category == 'stat.*':
                expanded.extend(stat_categories)
            else:
                expanded.append(category)
        
        return list(set(expanded))  # Remove duplicates
    
    async def search_papers(self, 
                          categories: List[str],
                          start_date: datetime,
                          end_date: Optional[datetime] = None,
                          max_results: int = 1000) -> List[ArxivPaper]:
        """
        Search for papers in specified categories and date range.
        
        Args:
            categories: List of arXiv categories to search (may include wildcards)
            start_date: Start date for paper search
            end_date: End date for paper search (default: now)
            max_results: Maximum number of results per request
            
        Returns:
            List of ArxivPaper objects
        """
        if end_date is None:
            end_date = datetime.now()
        
        # Expand wildcard categories
        expanded_categories = self._expand_wildcard_categories(categories)
        logger.info(f"Expanded categories: {expanded_categories}")
        
        all_papers = []
        
        for category in expanded_categories:
            logger.info(f"Searching papers in category: {category}")
            
            try:
                papers = await self._search_category(category, start_date, end_date, max_results)
                all_papers.extend(papers)
                logger.info(f"Found {len(papers)} papers in {category}")
                
            except Exception as e:
                logger.error(f"Failed to search category {category}: {e}")
                continue
        
        # Remove duplicates based on arXiv ID
        unique_papers = {}
        for paper in all_papers:
            if paper.arxiv_id not in unique_papers:
                unique_papers[paper.arxiv_id] = paper
        
        logger.info(f"Total unique papers found: {len(unique_papers)}")
        return list(unique_papers.values())
    
    async def _search_category(self, 
                             category: str,
                             start_date: datetime,
                             end_date: datetime,
                             max_results: int) -> List[ArxivPaper]:
        """Search papers in a specific category."""
        papers = []
        start_index = 0
        batch_size = min(max_results, 1000)  # arXiv API limit
        
        while True:
            await self._rate_limit()
            
            # Build query parameters
            query_params = {
                'search_query': f'cat:{category}',
                'start': start_index,
                'max_results': batch_size,
                'sortBy': 'submittedDate',
                'sortOrder': 'descending'
            }
            
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"{self.base_url}?{urlencode(query_params)}"
                    
                    async with session.get(url) as response:
                        if response.status != 200:
                            logger.error(f"API request failed: {response.status}")
                            break
                        
                        content = await response.text()
                        batch_papers = self._parse_arxiv_response(content, start_date, end_date)
                        
                        if not batch_papers:
                            break  # No more papers in date range
                        
                        papers.extend(batch_papers)
                        
                        # Check if we've reached the date limit
                        if batch_papers[-1].published_date < start_date:
                            break
                        
                        start_index += batch_size
                        
                        # Limit total results
                        if len(papers) >= max_results:
                            papers = papers[:max_results]
                            break
                            
            except Exception as e:
                logger.error(f"Error in API request: {e}")
                break
        
        return papers 
   
    def _parse_arxiv_response(self, 
                            xml_content: str,
                            start_date: datetime,
                            end_date: datetime) -> List[ArxivPaper]:
        """Parse arXiv API XML response into ArxivPaper objects."""
        papers = []
        
        try:
            root = ET.fromstring(xml_content)
            
            # Define namespaces
            namespaces = {
                'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom'
            }
            
            entries = root.findall('atom:entry', namespaces)
            
            for entry in entries:
                try:
                    # Extract basic information
                    arxiv_id = entry.find('atom:id', namespaces).text.split('/')[-1]
                    title = entry.find('atom:title', namespaces).text.strip()
                    abstract = entry.find('atom:summary', namespaces).text.strip()
                    
                    # Extract dates
                    published_str = entry.find('atom:published', namespaces).text
                    updated_str = entry.find('atom:updated', namespaces).text
                    
                    published_date = datetime.fromisoformat(published_str.replace('Z', '+00:00')).replace(tzinfo=None)
                    updated_date = datetime.fromisoformat(updated_str.replace('Z', '+00:00')).replace(tzinfo=None)
                    
                    # Filter by date range
                    if published_date < start_date or published_date > end_date:
                        continue
                    
                    # Extract authors
                    authors = []
                    author_elements = entry.findall('atom:author', namespaces)
                    for author_elem in author_elements:
                        name_elem = author_elem.find('atom:name', namespaces)
                        if name_elem is not None:
                            authors.append(name_elem.text.strip())
                    
                    # Extract categories
                    categories = []
                    category_elements = entry.findall('atom:category', namespaces)
                    for cat_elem in category_elements:
                        term = cat_elem.get('term')
                        if term:
                            categories.append(term)
                    
                    # Extract DOI if available
                    doi = None
                    doi_elem = entry.find('arxiv:doi', namespaces)
                    if doi_elem is not None:
                        doi = doi_elem.text.strip()
                    
                    # Build PDF URL
                    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
                    
                    # Create ArxivPaper object
                    paper = ArxivPaper(
                        paper_id=arxiv_id,
                        title=title,
                        authors=authors,
                        abstract=abstract,
                        published_date=published_date,
                        source_type='arxiv',
                        instance_name='quant_scholar',
                        arxiv_id=arxiv_id,
                        categories=categories,
                        updated_date=updated_date,
                        pdf_url=pdf_url,
                        doi=doi,
                        metadata={
                            'source': 'arxiv_api',
                            'discovered_at': datetime.now().isoformat()
                        }
                    )
                    
                    papers.append(paper)
                    
                except Exception as e:
                    logger.error(f"Failed to parse entry: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Failed to parse XML response: {e}")
        
        return papers


class JournalSourceHandler:
    """Base class for journal source handlers."""
    
    def __init__(self, instance_name: str, base_url: str):
        self.instance_name = instance_name
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=300),
            connector=aiohttp.TCPConnector(limit=5)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def discover_papers(self, 
                            start_date: datetime, 
                            end_date: datetime) -> List[JournalPaper]:
        """Discover papers from this journal source."""
        raise NotImplementedError("Subclasses must implement discover_papers")
    
    async def download_paper(self, paper: JournalPaper, download_dir: Path) -> Optional[str]:
        """Download a specific paper PDF."""
        raise NotImplementedError("Subclasses must implement download_paper")


class JStatSoftwareHandler(JournalSourceHandler):
    """Handler for Journal of Statistical Software."""
    
    def __init__(self, instance_name: str):
        super().__init__(instance_name, "https://www.jstatsoft.org")
    
    async def discover_papers(self, 
                            start_date: datetime, 
                            end_date: datetime) -> List[JournalPaper]:
        """
        Discover papers from Journal of Statistical Software.
        
        Args:
            start_date: Start date for paper search
            end_date: End date for paper search
            
        Returns:
            List of JournalPaper objects
        """
        papers = []
        
        try:
            # Get the main index page
            async with self.session.get(f"{self.base_url}/index") as response:
                if response.status != 200:
                    logger.error(f"Failed to access JSS index: {response.status}")
                    return papers
                
                content = await response.text()
                
                # Parse the HTML to find recent issues
                # This is a simplified implementation - would need proper HTML parsing
                import re
                
                # Look for volume/issue patterns in the HTML
                volume_pattern = r'href="(/article/view/v\d+i\d+)"'
                matches = re.findall(volume_pattern, content)
                
                for match in matches[:10]:  # Limit to recent issues
                    try:
                        issue_papers = await self._parse_issue(match, start_date, end_date)
                        papers.extend(issue_papers)
                    except Exception as e:
                        logger.error(f"Failed to parse JSS issue {match}: {e}")
                        continue
                
        except Exception as e:
            logger.error(f"Failed to discover JSS papers: {e}")
        
        return papers
    
    async def _parse_issue(self, 
                          issue_path: str, 
                          start_date: datetime, 
                          end_date: datetime) -> List[JournalPaper]:
        """Parse a specific JSS issue for papers."""
        papers = []
        
        try:
            async with self.session.get(f"{self.base_url}{issue_path}") as response:
                if response.status != 200:
                    return papers
                
                content = await response.text()
                
                # Extract paper information from issue page
                # This would need proper HTML parsing in a real implementation
                # For now, create a placeholder paper
                
                # Extract volume and issue from path
                volume_match = re.search(r'v(\d+)i(\d+)', issue_path)
                if volume_match:
                    volume = volume_match.group(1)
                    issue = volume_match.group(2)
                    
                    # Create a sample paper (in real implementation, would parse actual papers)
                    paper = JournalPaper(
                        paper_id=f"jss_v{volume}i{issue}",
                        title=f"JSS Volume {volume} Issue {issue} Sample Paper",
                        authors=["Sample Author"],
                        abstract="Sample abstract for JSS paper",
                        published_date=datetime.now(),  # Would extract actual date
                        source_type='journal',
                        instance_name=self.instance_name,
                        journal_name="Journal of Statistical Software",
                        volume=volume,
                        issue=issue,
                        pdf_url=f"{self.base_url}/article/download/{issue_path.split('/')[-1]}/pdf",
                        journal_url=f"{self.base_url}{issue_path}",
                        metadata={
                            'source': 'jss',
                            'discovered_at': datetime.now().isoformat()
                        }
                    )
                    
                    # Check if paper is in date range
                    if start_date <= paper.published_date <= end_date:
                        papers.append(paper)
                
        except Exception as e:
            logger.error(f"Failed to parse JSS issue {issue_path}: {e}")
        
        return papers
    
    async def download_paper(self, paper: JournalPaper, download_dir: Path) -> Optional[str]:
        """Download a JSS paper PDF."""
        try:
            filename = f"{paper.paper_id}.pdf"
            file_path = download_dir / filename
            
            # Skip if file already exists
            if file_path.exists():
                return str(file_path)
            
            async with self.session.get(paper.pdf_url) as response:
                if response.status == 200:
                    async with aiofiles.open(file_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)
                    
                    logger.info(f"Downloaded JSS paper: {filename}")
                    return str(file_path)
                else:
                    logger.error(f"Failed to download JSS paper {paper.paper_id}: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error downloading JSS paper {paper.paper_id}: {e}")
            return None


class RJournalHandler(JournalSourceHandler):
    """Handler for R Journal."""
    
    def __init__(self, instance_name: str):
        super().__init__(instance_name, "https://journal.r-project.org")
    
    async def discover_papers(self, 
                            start_date: datetime, 
                            end_date: datetime) -> List[JournalPaper]:
        """
        Discover papers from R Journal.
        
        Args:
            start_date: Start date for paper search
            end_date: End date for paper search
            
        Returns:
            List of JournalPaper objects
        """
        papers = []
        
        try:
            # Get the issues page
            async with self.session.get(f"{self.base_url}/issues.html") as response:
                if response.status != 200:
                    logger.error(f"Failed to access R Journal issues: {response.status}")
                    return papers
                
                content = await response.text()
                
                # Parse the HTML to find recent issues
                # This is a simplified implementation
                import re
                
                # Look for issue patterns in the HTML
                issue_pattern = r'href="(/archive/\d{4}-\d+/)"'
                matches = re.findall(issue_pattern, content)
                
                for match in matches[:5]:  # Limit to recent issues
                    try:
                        issue_papers = await self._parse_r_issue(match, start_date, end_date)
                        papers.extend(issue_papers)
                    except Exception as e:
                        logger.error(f"Failed to parse R Journal issue {match}: {e}")
                        continue
                
        except Exception as e:
            logger.error(f"Failed to discover R Journal papers: {e}")
        
        return papers
    
    async def _parse_r_issue(self, 
                           issue_path: str, 
                           start_date: datetime, 
                           end_date: datetime) -> List[JournalPaper]:
        """Parse a specific R Journal issue for papers."""
        papers = []
        
        try:
            async with self.session.get(f"{self.base_url}{issue_path}") as response:
                if response.status != 200:
                    return papers
                
                content = await response.text()
                
                # Extract year and issue from path
                year_issue_match = re.search(r'/(\d{4})-(\d+)/', issue_path)
                if year_issue_match:
                    year = year_issue_match.group(1)
                    issue = year_issue_match.group(2)
                    
                    # Create a sample paper (in real implementation, would parse actual papers)
                    paper = JournalPaper(
                        paper_id=f"rjournal_{year}_{issue}",
                        title=f"R Journal {year} Issue {issue} Sample Paper",
                        authors=["Sample R Author"],
                        abstract="Sample abstract for R Journal paper",
                        published_date=datetime(int(year), 1, 1),  # Would extract actual date
                        source_type='journal',
                        instance_name=self.instance_name,
                        journal_name="The R Journal",
                        volume=year,
                        issue=issue,
                        pdf_url=f"{self.base_url}/archive/{year}-{issue}/sample.pdf",
                        journal_url=f"{self.base_url}{issue_path}",
                        metadata={
                            'source': 'rjournal',
                            'discovered_at': datetime.now().isoformat()
                        }
                    )
                    
                    # Check if paper is in date range
                    if start_date <= paper.published_date <= end_date:
                        papers.append(paper)
                
        except Exception as e:
            logger.error(f"Failed to parse R Journal issue {issue_path}: {e}")
        
        return papers
    
    async def download_paper(self, paper: JournalPaper, download_dir: Path) -> Optional[str]:
        """Download an R Journal paper PDF."""
        try:
            filename = f"{paper.paper_id}.pdf"
            file_path = download_dir / filename
            
            # Skip if file already exists
            if file_path.exists():
                return str(file_path)
            
            async with self.session.get(paper.pdf_url) as response:
                if response.status == 200:
                    async with aiofiles.open(file_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)
                    
                    logger.info(f"Downloaded R Journal paper: {filename}")
                    return str(file_path)
                else:
                    logger.error(f"Failed to download R Journal paper {paper.paper_id}: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error downloading R Journal paper {paper.paper_id}: {e}")
            return None


class QuantScholarDownloader(BaseScholarDownloader):
    """Quant Scholar downloader for arXiv papers and journal sources."""
    
    def __init__(self, config_path: str = "configs/quant_scholar.yaml"):
        """
        Initialize Quant Scholar downloader.
        
        Args:
            config_path: Path to Quant Scholar configuration file
        """
        # Load configuration
        from ..config.instance_config_manager import InstanceConfigManager
        config_manager = InstanceConfigManager()
        instance_config = config_manager.load_config(config_path)
        
        super().__init__(instance_config)
        
        # Initialize arXiv API client
        self.arxiv_client = ArxivAPIClient()
        
        # Initialize journal handlers
        self.journal_handlers = {
            'jss': JStatSoftwareHandler(self.instance_name),
            'rjournal': RJournalHandler(self.instance_name)
        }
        
        # Initialize Quant Scholar processor
        self.processor: Optional[QuantScholarProcessor] = None
        
        # Initialize enhanced error handler
        self.quant_error_handler: Optional[QuantScholarErrorHandler] = None
        
        # Track processed papers for duplicate detection
        self.processed_papers: Set[str] = set()
        
        logger.info(f"QuantScholarDownloader initialized for categories: {self.config.arxiv_categories}")
        logger.info(f"Journal sources: {list(self.journal_handlers.keys())}")
    
    async def initialize_instance(self) -> bool:
        """Initialize the Quant Scholar instance with required components."""
        # Call parent initialization first
        success = await super().initialize_instance()
        if not success:
            return False
        
        try:
            # Initialize enhanced error handler
            if self.error_handler:
                error_dir = Path(self.config.storage_paths.error_log_directory).parent
                self.quant_error_handler = QuantScholarErrorHandler(
                    error_dir, self.instance_name, self.current_processor_id
                )
                logger.info("Enhanced Quant Scholar error handler initialized")
            
            # Initialize Quant Scholar processor
            self.processor = QuantScholarProcessor(self.config)
            processor_success = await self.processor.initialize()
            if not processor_success:
                logger.error("Failed to initialize Quant Scholar processor")
                return False
            
            # Load processed papers to avoid duplicates
            await self.load_processed_papers()
            
            logger.info(f"Quant Scholar instance '{self.instance_name}' fully initialized")
            return True
            
        except Exception as e:
            if self.quant_error_handler:
                self.quant_error_handler.log_quant_scholar_error(
                    e, 
                    {'operation': 'quant_scholar_initialization'},
                    ErrorCategory.CONFIGURATION,
                    ErrorSeverity.CRITICAL
                )
            logger.error(f"Failed to initialize Quant Scholar specific components: {e}")
            return False
    
    async def discover_papers(self, date_range: DateRange) -> List[BasePaper]:
        """
        Discover papers from arXiv and journal sources for Quant Scholar.
        
        Args:
            date_range: Date range to search for papers
            
        Returns:
            List of discovered papers (ArxivPaper and JournalPaper objects)
        """
        if not self.is_initialized:
            raise RuntimeError("Downloader not initialized")
        
        logger.info(f"Discovering Quant Scholar papers for date range: {date_range}")
        
        all_papers = []
        
        # Discover arXiv papers
        try:
            arxiv_papers = await self.discover_arxiv_papers(date_range)
            all_papers.extend(arxiv_papers)
            logger.info(f"Discovered {len(arxiv_papers)} arXiv papers")
        except Exception as e:
            if self.quant_error_handler:
                self.quant_error_handler.log_quant_scholar_error(
                    e,
                    {'operation': 'arxiv_discovery', 'date_range': str(date_range)},
                    ErrorCategory.ARXIV_API,
                    ErrorSeverity.ERROR
                )
            logger.error(f"Failed to discover arXiv papers: {e}")
        
        # Discover journal papers
        try:
            journal_papers = await self.discover_journal_papers(date_range)
            all_papers.extend(journal_papers)
            logger.info(f"Discovered {len(journal_papers)} journal papers")
        except Exception as e:
            if self.quant_error_handler:
                self.quant_error_handler.log_quant_scholar_error(
                    e,
                    {'operation': 'journal_discovery', 'date_range': str(date_range)},
                    ErrorCategory.JOURNAL_SOURCE,
                    ErrorSeverity.ERROR
                )
            logger.error(f"Failed to discover journal papers: {e}")
        
        # Filter out already processed papers
        new_papers = []
        for paper in all_papers:
            paper_id = paper.arxiv_id if hasattr(paper, 'arxiv_id') else paper.paper_id
            if paper_id not in self.processed_papers:
                new_papers.append(paper)
            else:
                logger.debug(f"Skipping already processed paper: {paper_id}")
        
        logger.info(f"Discovered {len(new_papers)} new papers total")
        return new_papers
    
    async def discover_arxiv_papers(self, date_range: DateRange) -> List[ArxivPaper]:
        """
        Discover arXiv papers for Quant Scholar categories with wildcard support.
        
        Args:
            date_range: Date range to search for papers
            
        Returns:
            List of discovered ArxivPaper objects
        """
        # Use enhanced error handling with retry
        async def _discover_operation():
            # Update progress tracker
            if self.progress_tracker:
                self.progress_tracker.start_operation("arxiv_discovery", len(self.config.arxiv_categories))
            
            # Search papers using arXiv API with wildcard support
            papers = await self.arxiv_client.search_papers(
                categories=self.config.arxiv_categories,
                start_date=date_range.start_date,
                end_date=date_range.end_date,
                max_results=10000  # Large limit for comprehensive search
            )
            
            # Update progress tracker
            if self.progress_tracker:
                self.progress_tracker.complete_operation("arxiv_discovery")
            
            return papers
        
        if self.quant_error_handler:
            success, papers, error = await self.quant_error_handler.handle_with_retry(
                _discover_operation,
                ErrorCategory.ARXIV_API,
                {'operation': 'arxiv_discovery', 'date_range': str(date_range)}
            )
            
            if not success:
                logger.error(f"Failed to discover arXiv papers after retries: {error}")
                raise error or Exception("ArXiv paper discovery failed")
            
            return papers
        else:
            # Fallback to direct execution
            try:
                return await _discover_operation()
            except Exception as e:
                if self.error_handler:
                    self.error_handler.log_instance_error(
                        e,
                        {'operation': 'arxiv_discovery', 'date_range': str(date_range)},
                        'arxiv_discovery_error'
                    )
                logger.error(f"Failed to discover arXiv papers: {e}")
                raise
    
    async def discover_journal_papers(self, date_range: DateRange) -> List[JournalPaper]:
        """
        Discover journal papers from configured journal sources.
        
        Args:
            date_range: Date range to search for papers
            
        Returns:
            List of discovered JournalPaper objects
        """
        all_journal_papers = []
        
        for source_name, handler in self.journal_handlers.items():
            try:
                logger.info(f"Discovering papers from {source_name}")
                
                async with handler:
                    papers = await handler.discover_papers(
                        date_range.start_date, 
                        date_range.end_date
                    )
                    all_journal_papers.extend(papers)
                    logger.info(f"Found {len(papers)} papers from {source_name}")
                
            except Exception as e:
                if self.quant_error_handler:
                    self.quant_error_handler.log_quant_scholar_error(
                        e,
                        {'operation': 'journal_discovery', 'source': source_name},
                        ErrorCategory.JOURNAL_SOURCE,
                        ErrorSeverity.ERROR
                    )
                logger.error(f"Failed to discover papers from {source_name}: {e}")
                continue
        
        return all_journal_papers
    
    async def download_papers(self, papers: List[BasePaper]) -> DownloadResult:
        """
        Download PDFs for the specified papers from arXiv and journal sources.
        
        Args:
            papers: List of papers to download (ArxivPaper and JournalPaper objects)
            
        Returns:
            DownloadResult with download statistics
        """
        if not self.is_initialized:
            raise RuntimeError("Downloader not initialized")
        
        if not papers:
            logger.info("No papers to download")
            return DownloadResult()
        
        logger.info(f"Starting download of {len(papers)} papers")
        
        # Separate arXiv and journal papers
        arxiv_papers = [p for p in papers if isinstance(p, ArxivPaper)]
        journal_papers = [p for p in papers if isinstance(p, JournalPaper)]
        
        logger.info(f"ArXiv papers: {len(arxiv_papers)}, Journal papers: {len(journal_papers)}")
        
        result = DownloadResult()
        download_dir = Path(self.config.storage_paths.pdf_directory)
        download_dir.mkdir(parents=True, exist_ok=True)
        
        # Download arXiv papers
        if arxiv_papers:
            try:
                arxiv_result = await self._download_arxiv_papers(arxiv_papers, download_dir)
                result.successful_downloads.extend(arxiv_result.successful_downloads)
                result.failed_downloads.extend(arxiv_result.failed_downloads)
                result.skipped_downloads.extend(arxiv_result.skipped_downloads)
                result.total_size_mb += arxiv_result.total_size_mb
            except Exception as e:
                if self.quant_error_handler:
                    self.quant_error_handler.log_quant_scholar_error(
                        e,
                        {'operation': 'arxiv_download', 'paper_count': len(arxiv_papers)},
                        ErrorCategory.DOWNLOAD,
                        ErrorSeverity.ERROR
                    )
                logger.error(f"Failed to download arXiv papers: {e}")
        
        # Download journal papers
        if journal_papers:
            try:
                journal_result = await self._download_journal_papers(journal_papers, download_dir)
                result.successful_downloads.extend(journal_result.successful_downloads)
                result.failed_downloads.extend(journal_result.failed_downloads)
                result.skipped_downloads.extend(journal_result.skipped_downloads)
                result.total_size_mb += journal_result.total_size_mb
            except Exception as e:
                if self.quant_error_handler:
                    self.quant_error_handler.log_quant_scholar_error(
                        e,
                        {'operation': 'journal_download', 'paper_count': len(journal_papers)},
                        ErrorCategory.JOURNAL_SOURCE,
                        ErrorSeverity.ERROR
                    )
                logger.error(f"Failed to download journal papers: {e}")
        
        logger.info(f"Download completed: {result.success_count} successful, "
                   f"{result.failure_count} failed, {result.skip_count} skipped")
        
        return result    

    async def _download_arxiv_papers(self, 
                                   papers: List[ArxivPaper], 
                                   download_dir: Path) -> DownloadResult:
        """Download arXiv papers using the same logic as AI Scholar."""
        from ..downloaders.ai_scholar_downloader import GCSDownloader
        
        result = DownloadResult()
        
        try:
            async with GCSDownloader(self.instance_name) as downloader:
                result = await downloader.download_papers(
                    papers=papers,
                    download_dir=download_dir,
                    max_concurrent=self.config.processing_config.max_concurrent_downloads
                )
        except Exception as e:
            logger.error(f"Failed to download arXiv papers: {e}")
            # Add failed papers to result
            for paper in papers:
                result.failed_downloads.append(paper.arxiv_id)
        
        return result
    
    async def _download_journal_papers(self, 
                                     papers: List[JournalPaper], 
                                     download_dir: Path) -> DownloadResult:
        """Download journal papers using appropriate handlers."""
        result = DownloadResult()
        
        # Group papers by source
        papers_by_source = {}
        for paper in papers:
            source = paper.metadata.get('source', 'unknown')
            if source not in papers_by_source:
                papers_by_source[source] = []
            papers_by_source[source].append(paper)
        
        # Download papers from each source
        for source, source_papers in papers_by_source.items():
            if source in self.journal_handlers:
                handler = self.journal_handlers[source]
                
                try:
                    async with handler:
                        for paper in source_papers:
                            try:
                                file_path = await handler.download_paper(paper, download_dir)
                                if file_path:
                                    result.successful_downloads.append(file_path)
                                    # Get file size
                                    file_size = Path(file_path).stat().st_size / (1024 * 1024)
                                    result.total_size_mb += file_size
                                else:
                                    result.failed_downloads.append(paper.paper_id)
                            except Exception as e:
                                logger.error(f"Failed to download {paper.paper_id}: {e}")
                                result.failed_downloads.append(paper.paper_id)
                
                except Exception as e:
                    logger.error(f"Failed to download papers from {source}: {e}")
                    for paper in source_papers:
                        result.failed_downloads.append(paper.paper_id)
            else:
                logger.warning(f"No handler for source: {source}")
                for paper in source_papers:
                    result.failed_downloads.append(paper.paper_id)
        
        return result
    
    async def process_papers(self, pdf_paths: List[str]) -> ProcessingResult:
        """
        Process downloaded PDFs into the vector store.
        
        Args:
            pdf_paths: List of PDF file paths to process
            
        Returns:
            ProcessingResult with processing statistics
        """
        if not self.is_initialized or not self.processor:
            raise RuntimeError("Downloader not initialized")
        
        if not pdf_paths:
            logger.info("No PDFs to process")
            return ProcessingResult()
        
        logger.info(f"Starting processing of {len(pdf_paths)} PDFs")
        
        start_time = time.time()
        
        # Use enhanced error handling with retry
        async def _process_operation():
            # Update progress tracker
            if self.progress_tracker:
                self.progress_tracker.start_operation("paper_processing", len(pdf_paths))
            
            # Use the Quant Scholar processor to process papers
            result = await self.processor.process_papers(pdf_paths)
            
            # Update progress tracker
            if self.progress_tracker:
                self.progress_tracker.complete_operation("paper_processing")
            
            return result
        
        if self.quant_error_handler:
            success, result, error = await self.quant_error_handler.handle_with_retry(
                _process_operation,
                ErrorCategory.PDF_PROCESSING,
                {'operation': 'paper_processing', 'pdf_count': len(pdf_paths)}
            )
            
            if not success:
                logger.error(f"Failed to process papers after retries: {error}")
                raise error or Exception("Paper processing failed")
            
            # Calculate final statistics
            result.processing_time_seconds = time.time() - start_time
            
            logger.info(f"Processing completed: {result.success_count} successful, "
                       f"{result.failure_count} failed, {result.skip_count} skipped")
            return result
        else:
            # Fallback to direct execution
            try:
                result = await _process_operation()
                result.processing_time_seconds = time.time() - start_time
                
                logger.info(f"Processing completed: {result.success_count} successful, "
                           f"{result.failure_count} failed, {result.skip_count} skipped")
                return result
            except Exception as e:
                if self.error_handler:
                    self.error_handler.log_instance_error(
                        e,
                        {'operation': 'paper_processing', 'pdf_count': len(pdf_paths)},
                        'paper_processing_error'
                    )
                logger.error(f"Failed to process papers: {e}")
                raise
    
    def _extract_paper_id_from_path(self, pdf_path: str) -> Optional[str]:
        """Extract paper ID from PDF file path."""
        try:
            filename = Path(pdf_path).stem
            # Handle both arXiv IDs and journal paper IDs
            if filename.startswith('jss_') or filename.startswith('rjournal_'):
                return filename
            else:
                # Assume arXiv ID format
                parts = filename.split('_')
                if len(parts) > 0:
                    # Convert back from safe filename format
                    paper_id = parts[0].replace('_', '/')
                    return paper_id
        except Exception:
            pass
        return None
    
    async def load_processed_papers(self) -> None:
        """Load list of already processed papers to avoid duplicates."""
        try:
            processed_list = []
            
            # Load from state manager if available
            if self.state_manager:
                state = self.state_manager.load_instance_state(self.instance_name)
                if state and hasattr(state, 'processed_files'):
                    # Extract paper IDs from processed files
                    for file_path in state.processed_files:
                        paper_id = self._extract_paper_id_from_path(file_path)
                        if paper_id:
                            self.processed_papers.add(paper_id)
                            processed_list.append(paper_id)
                    
                    logger.info(f"Loaded {len(self.processed_papers)} processed papers from state")
            
            # Load into processor if available
            if self.processor:
                self.processor.load_processed_documents(processed_list)
            
            # Also check vector store for existing documents
            if self.processor and self.processor.vector_store:
                try:
                    stats = self.processor.vector_store.get_instance_stats()
                    doc_count = stats.get('document_count', 0)
                    if doc_count > 0:
                        logger.info(f"Found {doc_count} existing documents in vector store")
                except Exception as e:
                    logger.warning(f"Could not check vector store stats: {e}")
                    
        except Exception as e:
            if self.quant_error_handler:
                self.quant_error_handler.log_quant_scholar_error(
                    e,
                    {'operation': 'load_processed_papers'},
                    ErrorCategory.STORAGE,
                    ErrorSeverity.WARNING
                )
            logger.error(f"Failed to load processed papers: {e}")
    
    def get_quant_scholar_stats(self) -> Dict[str, Any]:
        """Get comprehensive Quant Scholar statistics."""
        base_stats = self.get_instance_stats()
        
        quant_stats = {
            'instance_type': 'quant_scholar',
            'arxiv_categories': self.config.arxiv_categories,
            'journal_sources': list(self.journal_handlers.keys()),
            'processed_papers_count': len(self.processed_papers),
            'processor_initialized': self.processor is not None,
            'error_handler_initialized': self.quant_error_handler is not None
        }
        
        # Add processor stats if available
        if self.processor:
            try:
                processor_stats = self.processor.get_processing_stats()
                quant_stats['processor_stats'] = processor_stats
            except Exception as e:
                quant_stats['processor_stats_error'] = str(e)
        
        # Add error handler stats if available
        if self.quant_error_handler:
            try:
                error_stats = self.quant_error_handler.get_quant_scholar_error_summary()
                quant_stats['error_stats'] = error_stats
            except Exception as e:
                quant_stats['error_stats_error'] = str(e)
        
        return {**base_stats, **quant_stats}
    
    def should_continue_processing(self) -> bool:
        """Determine if Quant Scholar processing should continue."""
        # Check enhanced error handler first
        if self.quant_error_handler:
            if not self.quant_error_handler.should_continue_processing():
                logger.error("Quant Scholar error handler recommends stopping processing")
                return False
        
        # Use parent method for additional checks
        return super().should_continue_processing()
    
    async def export_quant_scholar_report(self, output_dir: Path) -> bool:
        """Export comprehensive Quant Scholar processing report."""
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate comprehensive report
            report = {
                'report_type': 'quant_scholar_processing_report',
                'generated_at': datetime.now().isoformat(),
                'instance_stats': self.get_quant_scholar_stats(),
                'configuration': {
                    'arxiv_categories': self.config.arxiv_categories,
                    'journal_sources': list(self.journal_handlers.keys()),
                    'storage_paths': self.config.storage_paths.to_dict(),
                    'processing_config': self.config.processing_config.to_dict()
                }
            }
            
            # Export main report
            report_path = output_dir / f"quant_scholar_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            # Export error report if error handler available
            if self.quant_error_handler:
                error_report_path = output_dir / f"quant_scholar_errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                self.quant_error_handler.export_quant_scholar_report(error_report_path)
            
            logger.info(f"Quant Scholar reports exported to {output_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export Quant Scholar report: {e}")
            return False