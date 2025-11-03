"""
AI Scholar Downloader for multi-instance ArXiv system.

Specialized downloader for AI Scholar instance that handles:
- arXiv categories: cond-mat, gr-qc, hep-ph, hep-th, math, math-ph, physics, q-alg, quant-ph
- Google Cloud Storage bulk download integration
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

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from ..base.base_scholar_downloader import (
    BaseScholarDownloader, DateRange, DownloadResult, ProcessingResult
)
from ..shared.multi_instance_data_models import (
    ArxivPaper, InstanceConfig, UpdateReport
)
from ..processors.ai_scholar_processor import AIScholarProcessor
from ..error_handling.ai_scholar_error_handler import (
    AIScholarErrorHandler, ErrorCategory, ErrorSeverity
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
    """Client for arXiv API to discover papers and metadata."""
    
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
    
    async def search_papers(self, 
                          categories: List[str],
                          start_date: datetime,
                          end_date: Optional[datetime] = None,
                          max_results: int = 1000) -> List[ArxivPaper]:
        """
        Search for papers in specified categories and date range.
        
        Args:
            categories: List of arXiv categories to search
            start_date: Start date for paper search
            end_date: End date for paper search (default: now)
            max_results: Maximum number of results per request
            
        Returns:
            List of ArxivPaper objects
        """
        if end_date is None:
            end_date = datetime.now()
        
        all_papers = []
        
        for category in categories:
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
                        instance_name='ai_scholar',
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


class GCSDownloader:
    """Google Cloud Storage downloader for bulk arXiv data."""
    
    def __init__(self, instance_name: str):
        self.instance_name = instance_name
        self.gcs_base_url = "https://storage.googleapis.com/arxiv-dataset/arxiv/arxiv/pdf"
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=300),  # 5 minute timeout
            connector=aiohttp.TCPConnector(limit=10)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def download_papers(self, 
                            papers: List[ArxivPaper],
                            download_dir: Path,
                            max_concurrent: int = 5) -> DownloadResult:
        """
        Download PDFs for the specified papers from Google Cloud Storage.
        
        Args:
            papers: List of papers to download
            download_dir: Directory to save PDFs
            max_concurrent: Maximum concurrent downloads
            
        Returns:
            DownloadResult with download statistics
        """
        result = DownloadResult()
        download_dir.mkdir(parents=True, exist_ok=True)
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)
        
        # Track download progress
        start_time = time.time()
        
        # Create download tasks
        tasks = []
        for paper in papers:
            task = self._download_paper_with_semaphore(semaphore, paper, download_dir, result)
            tasks.append(task)
        
        # Execute downloads
        logger.info(f"Starting download of {len(papers)} papers with {max_concurrent} concurrent downloads")
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Calculate statistics
        result.download_time_seconds = time.time() - start_time
        
        logger.info(f"Download completed: {result.success_count} successful, "
                   f"{result.failure_count} failed, {result.skip_count} skipped")
        
        return result
    
    async def _download_paper_with_semaphore(self,
                                           semaphore: asyncio.Semaphore,
                                           paper: ArxivPaper,
                                           download_dir: Path,
                                           result: DownloadResult) -> None:
        """Download a single paper with semaphore control."""
        async with semaphore:
            await self._download_single_paper(paper, download_dir, result)
    
    async def _download_single_paper(self,
                                   paper: ArxivPaper,
                                   download_dir: Path,
                                   result: DownloadResult) -> None:
        """Download a single paper PDF."""
        try:
            # Generate filename
            filename = paper.get_filename()
            file_path = download_dir / filename
            
            # Skip if file already exists
            if file_path.exists():
                result.skipped_downloads.append(str(file_path))
                logger.debug(f"Skipping existing file: {filename}")
                return
            
            # Try GCS first, then fallback to arXiv
            success = False
            
            # Try Google Cloud Storage
            gcs_url = f"{self.gcs_base_url}/{paper.arxiv_id}.pdf"
            success = await self._download_from_url(gcs_url, file_path, result)
            
            # Fallback to arXiv if GCS fails
            if not success:
                logger.debug(f"GCS download failed for {paper.arxiv_id}, trying arXiv")
                success = await self._download_from_url(paper.pdf_url, file_path, result)
            
            if success:
                result.successful_downloads.append(str(file_path))
                logger.debug(f"Successfully downloaded: {filename}")
            else:
                result.failed_downloads.append(paper.arxiv_id)
                logger.error(f"Failed to download: {paper.arxiv_id}")
                
        except Exception as e:
            result.failed_downloads.append(paper.arxiv_id)
            logger.error(f"Error downloading {paper.arxiv_id}: {e}")
    
    async def _download_from_url(self, url: str, file_path: Path, result: DownloadResult) -> bool:
        """Download file from URL."""
        try:
            if not self.session:
                return False
                
            async with self.session.get(url) as response:
                if response.status == 200:
                    # Create temporary file first
                    temp_path = file_path.with_suffix('.tmp')
                    
                    async with aiofiles.open(temp_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)
                    
                    # Move to final location
                    temp_path.rename(file_path)
                    
                    # Update size statistics
                    file_size = file_path.stat().st_size
                    result.total_size_mb += file_size / (1024 * 1024)
                    
                    return True
                else:
                    logger.debug(f"HTTP {response.status} for URL: {url}")
                    return False
                    
        except Exception as e:
            logger.debug(f"Download error for {url}: {e}")
            return False


class AIScholarDownloader(BaseScholarDownloader):
    """AI Scholar downloader for arXiv papers in AI and physics categories."""
    
    def __init__(self, config_path: str = "configs/ai_scholar.yaml"):
        """
        Initialize AI Scholar downloader.
        
        Args:
            config_path: Path to AI Scholar configuration file
        """
        # Load configuration
        from ..config.instance_config_manager import InstanceConfigManager
        config_manager = InstanceConfigManager(instance_name="ai_scholar", config_file=config_path)
        instance_config = config_manager.get_instance_config()
        
        super().__init__(instance_config)
        
        # Initialize arXiv API client
        self.arxiv_client = ArxivAPIClient()
        
        # Initialize AI Scholar processor
        self.processor: Optional[AIScholarProcessor] = None
        
        # Initialize enhanced error handler
        self.ai_error_handler: Optional[AIScholarErrorHandler] = None
        
        # Track processed papers for duplicate detection
        self.processed_papers: Set[str] = set()
        
        logger.info(f"AIScholarDownloader initialized for categories: {self.config.arxiv_categories}")
    
    async def initialize_instance(self) -> bool:
        """Initialize the AI Scholar instance with required components."""
        # Call parent initialization first
        success = await super().initialize_instance()
        if not success:
            return False
        
        try:
            # Initialize enhanced error handler
            if self.error_handler:
                error_dir = Path(self.config.storage_paths.error_log_directory).parent
                self.ai_error_handler = AIScholarErrorHandler(
                    error_dir, self.instance_name, self.current_processor_id
                )
                logger.info("Enhanced AI Scholar error handler initialized")
            
            # Initialize AI Scholar processor
            self.processor = AIScholarProcessor(self.config)
            processor_success = await self.processor.initialize()
            if not processor_success:
                logger.error("Failed to initialize AI Scholar processor")
                return False
            
            # Load processed papers to avoid duplicates
            await self.load_processed_papers()
            
            logger.info(f"AI Scholar instance '{self.instance_name}' fully initialized")
            return True
            
        except Exception as e:
            if self.ai_error_handler:
                self.ai_error_handler.log_ai_scholar_error(
                    e, 
                    {'operation': 'ai_scholar_initialization'},
                    ErrorCategory.CONFIGURATION,
                    ErrorSeverity.CRITICAL
                )
            logger.error(f"Failed to initialize AI Scholar specific components: {e}")
            return False
    
    async def discover_papers(self, date_range: DateRange) -> List[ArxivPaper]:
        """
        Discover arXiv papers for AI Scholar categories.
        
        Args:
            date_range: Date range to search for papers
            
        Returns:
            List of discovered ArxivPaper objects
        """
        if not self.is_initialized:
            raise RuntimeError("Downloader not initialized")
        
        logger.info(f"Discovering AI Scholar papers for date range: {date_range}")
        
        # Use enhanced error handling with retry
        async def _discover_operation():
            # Update progress tracker
            if self.progress_tracker:
                self.progress_tracker.start_operation("paper_discovery", len(self.config.arxiv_categories))
            
            # Search papers using arXiv API
            papers = await self.arxiv_client.search_papers(
                categories=self.config.arxiv_categories,
                start_date=date_range.start_date,
                end_date=date_range.end_date,
                max_results=10000  # Large limit for comprehensive search
            )
            
            # Filter out already processed papers
            new_papers = []
            for paper in papers:
                if paper.arxiv_id not in self.processed_papers:
                    new_papers.append(paper)
                else:
                    logger.debug(f"Skipping already processed paper: {paper.arxiv_id}")
            
            # Update progress tracker
            if self.progress_tracker:
                self.progress_tracker.complete_operation("paper_discovery")
            
            return new_papers
        
        if self.ai_error_handler:
            success, papers, error = await self.ai_error_handler.handle_with_retry(
                _discover_operation,
                ErrorCategory.ARXIV_API,
                {'operation': 'paper_discovery', 'date_range': str(date_range)}
            )
            
            if not success:
                logger.error(f"Failed to discover papers after retries: {error}")
                raise error or Exception("Paper discovery failed")
            
            logger.info(f"Discovered {len(papers)} new papers")
            return papers
        else:
            # Fallback to direct execution if enhanced error handler not available
            try:
                papers = await _discover_operation()
                logger.info(f"Discovered {len(papers)} new papers")
                return papers
            except Exception as e:
                if self.error_handler:
                    self.error_handler.log_instance_error(
                        e,
                        {'operation': 'paper_discovery', 'date_range': str(date_range)},
                        'paper_discovery_error'
                    )
                logger.error(f"Failed to discover papers: {e}")
                raise
    
    async def download_papers(self, papers: List[ArxivPaper]) -> DownloadResult:
        """
        Download PDFs for the specified papers.
        
        Args:
            papers: List of ArxivPaper objects to download
            
        Returns:
            DownloadResult with download statistics
        """
        if not self.is_initialized:
            raise RuntimeError("Downloader not initialized")
        
        if not papers:
            logger.info("No papers to download")
            return DownloadResult()
        
        logger.info(f"Starting download of {len(papers)} papers")
        
        # Use enhanced error handling with retry
        async def _download_operation():
            # Update progress tracker
            if self.progress_tracker:
                self.progress_tracker.start_operation("paper_download", len(papers))
            
            # Create download directory
            download_dir = Path(self.config.storage_paths.pdf_directory)
            
            # Download papers using GCS downloader
            async with GCSDownloader(self.instance_name) as downloader:
                result = await downloader.download_papers(
                    papers=papers,
                    download_dir=download_dir,
                    max_concurrent=self.config.processing_config.max_concurrent_downloads
                )
            
            # Update progress tracker
            if self.progress_tracker:
                self.progress_tracker.complete_operation("paper_download")
            
            return result
        
        if self.ai_error_handler:
            success, result, error = await self.ai_error_handler.handle_with_retry(
                _download_operation,
                ErrorCategory.DOWNLOAD,
                {'operation': 'paper_download', 'paper_count': len(papers)}
            )
            
            if not success:
                logger.error(f"Failed to download papers after retries: {error}")
                raise error or Exception("Paper download failed")
            
            logger.info(f"Download completed: {result.success_count} successful, "
                       f"{result.failure_count} failed, {result.skip_count} skipped")
            return result
        else:
            # Fallback to direct execution
            try:
                result = await _download_operation()
                logger.info(f"Download completed: {result.success_count} successful, "
                           f"{result.failure_count} failed, {result.skip_count} skipped")
                return result
            except Exception as e:
                if self.error_handler:
                    self.error_handler.log_instance_error(
                        e,
                        {'operation': 'paper_download', 'paper_count': len(papers)},
                        'paper_download_error'
                    )
                logger.error(f"Failed to download papers: {e}")
                raise
    
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
            
            # Use the AI Scholar processor to process papers
            result = await self.processor.process_papers(pdf_paths)
            
            # Update progress tracker
            if self.progress_tracker:
                self.progress_tracker.complete_operation("paper_processing")
            
            return result
        
        if self.ai_error_handler:
            success, result, error = await self.ai_error_handler.handle_with_retry(
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

    
    def _extract_arxiv_id_from_path(self, pdf_path: str) -> Optional[str]:
        """Extract arXiv ID from PDF file path."""
        try:
            filename = Path(pdf_path).stem
            # Assume filename starts with arXiv ID
            parts = filename.split('_')
            if len(parts) > 0:
                # Convert back from safe filename format
                arxiv_id = parts[0].replace('_', '/')
                return arxiv_id
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
                    # Extract arXiv IDs from processed files
                    for file_path in state.processed_files:
                        arxiv_id = self._extract_arxiv_id_from_path(file_path)
                        if arxiv_id:
                            self.processed_papers.add(arxiv_id)
                            processed_list.append(arxiv_id)
                    
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
                    logger.warning(f"Could not check vector store for existing documents: {e}")
                    
        except Exception as e:
            if self.ai_error_handler:
                self.ai_error_handler.log_ai_scholar_error(
                    e,
                    {'operation': 'load_processed_papers'},
                    ErrorCategory.STORAGE,
                    ErrorSeverity.WARNING
                )
            logger.error(f"Failed to load processed papers: {e}")
    
    def get_ai_scholar_stats(self) -> Dict[str, Any]:
        """Get comprehensive AI Scholar statistics."""
        base_stats = self.get_instance_stats()
        
        ai_stats = {
            'instance_type': 'ai_scholar',
            'arxiv_categories': self.config.arxiv_categories,
            'processed_papers_count': len(self.processed_papers),
            'processor_initialized': self.processor is not None,
            'error_handler_initialized': self.ai_error_handler is not None
        }
        
        # Add processor stats if available
        if self.processor:
            try:
                processor_stats = self.processor.get_processing_stats()
                ai_stats['processor_stats'] = processor_stats
            except Exception as e:
                ai_stats['processor_stats_error'] = str(e)
        
        # Add error handler stats if available
        if self.ai_error_handler:
            try:
                error_stats = self.ai_error_handler.get_ai_scholar_error_summary()
                ai_stats['error_stats'] = error_stats
            except Exception as e:
                ai_stats['error_stats_error'] = str(e)
        
        return {**base_stats, **ai_stats}
    
    def should_continue_processing(self) -> bool:
        """Determine if AI Scholar processing should continue."""
        # Check enhanced error handler first
        if self.ai_error_handler:
            if not self.ai_error_handler.should_continue_processing():
                logger.error("AI Scholar error handler recommends stopping processing")
                return False
        
        # Use parent method for additional checks
        return super().should_continue_processing()
    
    async def export_ai_scholar_report(self, output_dir: Path) -> bool:
        """Export comprehensive AI Scholar processing report."""
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate comprehensive report
            report = {
                'report_type': 'ai_scholar_processing_report',
                'generated_at': datetime.now().isoformat(),
                'instance_stats': self.get_ai_scholar_stats(),
                'configuration': {
                    'arxiv_categories': self.config.arxiv_categories,
                    'storage_paths': self.config.storage_paths.to_dict(),
                    'processing_config': self.config.processing_config.to_dict()
                }
            }
            
            # Export main report
            report_path = output_dir / f"ai_scholar_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            # Export error report if error handler available
            if self.ai_error_handler:
                error_report_path = output_dir / f"ai_scholar_errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                self.ai_error_handler.export_ai_scholar_report(error_report_path)
            
            logger.info(f"AI Scholar reports exported to {output_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export AI Scholar report: {e}")
            return False