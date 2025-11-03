"""
Bulk arXiv Downloader for arXiv RAG Enhancement system.

Downloads and processes papers from arXiv bulk data repository, with support for:
- arXiv API client for paper metadata discovery
- Google Cloud Storage bulk download
- Category and date range filtering
- Duplicate detection and resume functionality
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

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from ..shared import (
    StateManager, 
    ProgressTracker, 
    ErrorHandler,
    ProcessingState,
    ArxivPaper,
    DownloadStats
)

# Import existing services
try:
    from services.scientific_pdf_processor import scientific_pdf_processor
    from services.vector_store_service import vector_store_service
    from services.scientific_rag_service import scientific_rag_service
except ImportError as e:
    logging.warning(f"Could not import existing services: {e}")
    scientific_pdf_processor = None
    vector_store_service = None
    scientific_rag_service = None

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
                    for author in author_elements:
                        name = author.find('atom:name', namespaces)
                        if name is not None:
                            authors.append(name.text)
                    
                    # Extract categories
                    categories = []
                    category_elements = entry.findall('atom:category', namespaces)
                    for category in category_elements:
                        term = category.get('term')
                        if term:
                            categories.append(term)
                    
                    # Build PDF URL
                    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
                    
                    # Create ArxivPaper object
                    paper = ArxivPaper(
                        arxiv_id=arxiv_id,
                        title=title,
                        authors=authors,
                        categories=categories,
                        published_date=published_date,
                        updated_date=updated_date,
                        abstract=abstract,
                        pdf_url=pdf_url,
                        metadata={
                            'source': 'arxiv_api',
                            'discovery_date': datetime.now().isoformat()
                        }
                    )
                    
                    papers.append(paper)
                    
                except Exception as e:
                    logger.warning(f"Failed to parse entry: {e}")
                    continue
        
        except ET.ParseError as e:
            logger.error(f"Failed to parse XML response: {e}")
        
        return papers


class GCSDownloader:
    """Downloads PDFs from Google Cloud Storage bulk repository."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # GCS bucket information
        self.gcs_base_url = "https://storage.googleapis.com/arxiv-dataset/arxiv/pdf"
        
        # Download statistics
        self.download_stats = DownloadStats()
        
    async def download_papers(self, 
                            papers: List[ArxivPaper],
                            progress_tracker: ProgressTracker) -> List[Path]:
        """
        Download PDF files for the given papers.
        
        Args:
            papers: List of ArxivPaper objects to download
            progress_tracker: Progress tracker for monitoring
            
        Returns:
            List of successfully downloaded file paths
        """
        downloaded_files = []
        self.download_stats.total_papers = len(papers)
        self.download_stats.start_time = datetime.now()
        
        # Create semaphore for concurrent downloads
        semaphore = asyncio.Semaphore(5)  # Limit concurrent downloads
        
        async def download_single_paper(paper: ArxivPaper) -> Optional[Path]:
            async with semaphore:
                return await self._download_single_pdf(paper)
        
        # Create download tasks
        tasks = [download_single_paper(paper) for paper in papers]
        
        # Process downloads with progress tracking
        for i, task in enumerate(asyncio.as_completed(tasks)):
            try:
                result = await task
                
                if result:
                    downloaded_files.append(result)
                    self.download_stats.downloaded_count += 1
                else:
                    self.download_stats.failed_count += 1
                
                # Update progress
                progress_tracker.update_progress(
                    self.download_stats.downloaded_count + self.download_stats.failed_count,
                    f"Downloaded: {len(downloaded_files)}"
                )
                
            except Exception as e:
                logger.error(f"Download task failed: {e}")
                self.download_stats.failed_count += 1
        
        logger.info(f"Download complete: {len(downloaded_files)} successful, {self.download_stats.failed_count} failed")
        return downloaded_files
    
    async def _download_single_pdf(self, paper: ArxivPaper) -> Optional[Path]:
        """Download a single PDF file."""
        try:
            # Determine output path
            category_dir = self.output_dir / "pdfs" / paper.categories[0] if paper.categories else self.output_dir / "pdfs" / "unknown"
            category_dir.mkdir(parents=True, exist_ok=True)
            
            output_path = category_dir / paper.get_filename()
            
            # Skip if already exists
            if output_path.exists():
                logger.debug(f"File already exists: {output_path}")
                return output_path
            
            # Try direct arXiv download first
            success = await self._download_from_arxiv(paper.pdf_url, output_path)
            
            if not success:
                # Try GCS download as fallback
                gcs_url = self._build_gcs_url(paper.arxiv_id)
                success = await self._download_from_url(gcs_url, output_path)
            
            if success:
                logger.debug(f"Downloaded: {paper.arxiv_id}")
                return output_path
            else:
                logger.warning(f"Failed to download: {paper.arxiv_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading {paper.arxiv_id}: {e}")
            return None
    
    async def _download_from_arxiv(self, url: str, output_path: Path) -> bool:
        """Download PDF from arXiv directly."""
        return await self._download_from_url(url, output_path)
    
    async def _download_from_url(self, url: str, output_path: Path) -> bool:
        """Download PDF from given URL."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        async with aiofiles.open(output_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                await f.write(chunk)
                        
                        # Verify file was downloaded correctly
                        if output_path.exists() and output_path.stat().st_size > 0:
                            return True
                        else:
                            output_path.unlink(missing_ok=True)
                            return False
                    else:
                        logger.debug(f"Download failed with status {response.status}: {url}")
                        return False
                        
        except Exception as e:
            logger.debug(f"Download error for {url}: {e}")
            return False
    
    def _build_gcs_url(self, arxiv_id: str) -> str:
        """Build Google Cloud Storage URL for arXiv paper."""
        # arXiv ID format: YYMM.NNNN or subject-class/YYMMnnn
        if '/' in arxiv_id:
            # Old format: subject-class/YYMMnnn
            parts = arxiv_id.split('/')
            subject_class = parts[0]
            paper_id = parts[1]
            return f"{self.gcs_base_url}/{subject_class}/{paper_id}.pdf"
        else:
            # New format: YYMM.NNNN
            year_month = arxiv_id[:4]
            return f"{self.gcs_base_url}/{year_month}/{arxiv_id}.pdf"
    
    def get_download_stats(self) -> Dict[str, Any]:
        """Get current download statistics."""
        return self.download_stats.to_dict()


class CategoryFilter:
    """Filters papers by specified arXiv categories."""
    
    def __init__(self, target_categories: List[str]):
        self.target_categories = set(target_categories)
    
    def filter_papers(self, papers: List[ArxivPaper]) -> List[ArxivPaper]:
        """Filter papers by target categories."""
        filtered_papers = []
        
        for paper in papers:
            # Check if any of the paper's categories match our targets
            if any(cat in self.target_categories for cat in paper.categories):
                filtered_papers.append(paper)
        
        logger.info(f"Filtered {len(papers)} papers to {len(filtered_papers)} matching target categories")
        return filtered_papers


class DateRangeFilter:
    """Filters papers by publication date range."""
    
    def __init__(self, start_date: datetime, end_date: Optional[datetime] = None):
        self.start_date = start_date
        self.end_date = end_date or datetime.now()
    
    def filter_papers(self, papers: List[ArxivPaper]) -> List[ArxivPaper]:
        """Filter papers by date range."""
        filtered_papers = []
        
        for paper in papers:
            if self.start_date <= paper.published_date <= self.end_date:
                filtered_papers.append(paper)
        
        logger.info(f"Filtered {len(papers)} papers to {len(filtered_papers)} in date range {self.start_date.date()} to {self.end_date.date()}")
        return filtered_papers


class DuplicateDetector:
    """Detects and prevents reprocessing of existing papers."""
    
    def __init__(self, processed_papers_file: Path):
        self.processed_papers_file = processed_papers_file
        self.processed_papers: Set[str] = set()
        self._load_processed_papers()
    
    def _load_processed_papers(self):
        """Load list of already processed papers."""
        try:
            if self.processed_papers_file.exists():
                with open(self.processed_papers_file, 'r') as f:
                    data = json.load(f)
                    self.processed_papers = set(data.get('processed_papers', []))
                logger.info(f"Loaded {len(self.processed_papers)} previously processed papers")
        except Exception as e:
            logger.warning(f"Could not load processed papers file: {e}")
            self.processed_papers = set()
    
    def filter_new_papers(self, papers: List[ArxivPaper]) -> List[ArxivPaper]:
        """Filter out papers that have already been processed."""
        new_papers = []
        
        for paper in papers:
            if paper.arxiv_id not in self.processed_papers:
                new_papers.append(paper)
        
        logger.info(f"Filtered {len(papers)} papers to {len(new_papers)} new papers (skipped {len(papers) - len(new_papers)} duplicates)")
        return new_papers
    
    def mark_as_processed(self, paper_ids: List[str]):
        """Mark papers as processed."""
        self.processed_papers.update(paper_ids)
        self._save_processed_papers()
    
    def _save_processed_papers(self):
        """Save processed papers list to file."""
        try:
            self.processed_papers_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'processed_papers': list(self.processed_papers),
                'last_updated': datetime.now().isoformat(),
                'total_count': len(self.processed_papers)
            }
            
            with open(self.processed_papers_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save processed papers file: {e}")


class ArxivBulkDownloader:
    """Main class for bulk downloading and processing arXiv papers."""
    
    def __init__(self, 
                 categories: List[str],
                 start_date: datetime,
                 output_dir: str = "/datapool/aischolar/arxiv-dataset-2024"):
        """
        Initialize ArxivBulkDownloader.
        
        Args:
            categories: List of arXiv categories to download
            start_date: Start date for paper search
            output_dir: Output directory for downloaded files
        """
        self.categories = categories
        self.start_date = start_date
        self.output_dir = Path(output_dir)
        
        # Create output directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.state_dir = self.output_dir / "processed" / "state_files"
        self.error_log_dir = self.output_dir / "processed" / "error_logs"
        self.metadata_dir = self.output_dir / "metadata"
        
        # Initialize components
        self.processor_id = f"bulk_downloader_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.state_manager = StateManager(self.state_dir)
        self.error_handler = ErrorHandler(self.error_log_dir, self.processor_id)
        self.progress_tracker = ProgressTracker()
        
        # Processing components
        self.api_client = ArxivAPIClient()
        self.gcs_downloader = GCSDownloader(self.output_dir)
        self.category_filter = CategoryFilter(categories)
        self.date_filter = DateRangeFilter(start_date)
        self.duplicate_detector = DuplicateDetector(self.metadata_dir / "processed_papers.json")
        
        # Statistics
        self.discovered_papers = 0
        self.downloaded_papers = 0
        self.processed_papers = 0
        self.failed_papers = 0
        
        logger.info(f"ArxivBulkDownloader initialized for categories: {categories}")
    
    async def discover_papers(self) -> List[ArxivPaper]:
        """
        Discover papers from arXiv API.
        
        Returns:
            List of discovered ArxivPaper objects
        """
        logger.info("Starting paper discovery...")
        
        try:
            # Search papers using API
            papers = await self.api_client.search_papers(
                categories=self.categories,
                start_date=self.start_date,
                max_results=10000  # Adjust as needed
            )
            
            # Apply filters
            papers = self.category_filter.filter_papers(papers)
            papers = self.date_filter.filter_papers(papers)
            papers = self.duplicate_detector.filter_new_papers(papers)
            
            self.discovered_papers = len(papers)
            logger.info(f"Discovered {len(papers)} new papers to process")
            
            # Save paper metadata
            await self._save_paper_metadata(papers)
            
            return papers
            
        except Exception as e:
            self.error_handler.log_error(
                e,
                {'operation': 'paper_discovery'},
                'paper_discovery_error'
            )
            logger.error(f"Paper discovery failed: {e}")
            return []
    
    async def download_papers(self, papers: List[ArxivPaper]) -> List[Path]:
        """
        Download PDF files for discovered papers.
        
        Args:
            papers: List of papers to download
            
        Returns:
            List of successfully downloaded file paths
        """
        if not papers:
            logger.info("No papers to download")
            return []
        
        logger.info(f"Starting download of {len(papers)} papers...")
        
        # Start progress tracking
        self.progress_tracker.start_tracking(len(papers))
        
        try:
            # Download papers
            downloaded_files = await self.gcs_downloader.download_papers(papers, self.progress_tracker)
            
            self.downloaded_papers = len(downloaded_files)
            
            # Mark successfully downloaded papers as processed (for download tracking)
            downloaded_paper_ids = []
            for i, file_path in enumerate(downloaded_files):
                if i < len(papers):
                    downloaded_paper_ids.append(papers[i].arxiv_id)
            
            # Finish progress tracking
            self.progress_tracker.finish("Download complete")
            
            logger.info(f"Downloaded {len(downloaded_files)} papers successfully")
            return downloaded_files
            
        except Exception as e:
            self.error_handler.log_error(
                e,
                {'operation': 'paper_download'},
                'paper_download_error'
            )
            logger.error(f"Paper download failed: {e}")
            return []
    
    async def process_downloaded_papers(self, pdf_paths: List[Path]) -> bool:
        """
        Process downloaded PDFs into the RAG system.
        
        Args:
            pdf_paths: List of PDF file paths to process
            
        Returns:
            True if processing successful
        """
        if not pdf_paths:
            logger.info("No papers to process")
            return True
        
        logger.info(f"Starting processing of {len(pdf_paths)} downloaded papers...")
        
        # Initialize services
        if not await self._initialize_services():
            return False
        
        # Start progress tracking
        self.progress_tracker.start_tracking(len(pdf_paths))
        
        processed_count = 0
        failed_count = 0
        
        try:
            # Process each PDF
            for i, pdf_path in enumerate(pdf_paths):
                try:
                    success = await self._process_single_pdf(pdf_path)
                    
                    if success:
                        processed_count += 1
                    else:
                        failed_count += 1
                    
                    # Update progress
                    self.progress_tracker.update_progress(
                        processed_count + failed_count,
                        pdf_path.name
                    )
                    
                except Exception as e:
                    self.error_handler.log_error(
                        e,
                        {'file_path': str(pdf_path), 'operation': 'pdf_processing'},
                        'pdf_processing_error'
                    )
                    failed_count += 1
            
            self.processed_papers = processed_count
            self.failed_papers = failed_count
            
            # Finish progress tracking
            self.progress_tracker.finish("Processing complete")
            
            logger.info(f"Processing complete: {processed_count} successful, {failed_count} failed")
            return True
            
        except Exception as e:
            self.error_handler.log_error(
                e,
                {'operation': 'batch_processing'},
                'batch_processing_error'
            )
            logger.error(f"Batch processing failed: {e}")
            return False
    
    async def _initialize_services(self) -> bool:
        """Initialize required services."""
        try:
            if not all([scientific_pdf_processor, vector_store_service, scientific_rag_service]):
                logger.error("Required services not available")
                return False
            
            # Configure vector store
            vector_store_service.chroma_host = "localhost"
            vector_store_service.chroma_port = 8082
            
            # Initialize vector store
            await vector_store_service.initialize()
            
            # Check health
            health = await vector_store_service.health_check()
            if health.get('status') != 'healthy':
                logger.warning(f"Vector store health: {health}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Service initialization failed: {e}")
            return False
    
    async def _process_single_pdf(self, pdf_path: Path) -> bool:
        """Process a single PDF file."""
        try:
            # Extract content
            document_data = scientific_pdf_processor.extract_comprehensive_content(str(pdf_path))
            
            if not document_data:
                raise ValueError("No content extracted from PDF")
            
            # Create chunks
            chunks = scientific_rag_service._create_scientific_chunks(document_data)
            
            if not chunks:
                raise ValueError("No chunks created from document")
            
            # Add to vector store
            result = await vector_store_service.add_document_chunks(
                document_data['document_id'],
                chunks
            )
            
            if not result or result.get('chunks_added', 0) == 0:
                raise ValueError("Failed to add chunks to vector store")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to process {pdf_path}: {e}")
            return False
    
    async def _save_paper_metadata(self, papers: List[ArxivPaper]):
        """Save paper metadata to file."""
        try:
            self.metadata_dir.mkdir(parents=True, exist_ok=True)
            
            metadata_file = self.metadata_dir / f"discovered_papers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            papers_data = {
                'discovery_date': datetime.now().isoformat(),
                'categories': self.categories,
                'start_date': self.start_date.isoformat(),
                'total_papers': len(papers),
                'papers': [paper.to_dict() for paper in papers]
            }
            
            with open(metadata_file, 'w') as f:
                json.dump(papers_data, f, indent=2)
            
            logger.info(f"Saved paper metadata to {metadata_file}")
            
        except Exception as e:
            logger.error(f"Failed to save paper metadata: {e}")
    
    def get_download_stats(self) -> Dict[str, Any]:
        """Get comprehensive download and processing statistics."""
        return {
            'processor_id': self.processor_id,
            'categories': self.categories,
            'start_date': self.start_date.isoformat(),
            'discovered_papers': self.discovered_papers,
            'downloaded_papers': self.downloaded_papers,
            'processed_papers': self.processed_papers,
            'failed_papers': self.failed_papers,
            'download_stats': self.gcs_downloader.get_download_stats(),
            'error_summary': self.error_handler.get_error_summary().to_dict()
        }