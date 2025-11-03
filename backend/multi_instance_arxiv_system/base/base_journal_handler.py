"""
Base Journal Handler for multi-instance ArXiv system.

Provides abstract base class for implementing journal-specific handlers
for downloading papers from various journal sources.
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import aiohttp
import time

from ..shared.multi_instance_data_models import JournalPaper

logger = logging.getLogger(__name__)


class JournalMetadata:
    """Metadata extracted from journal papers."""
    
    def __init__(self):
        self.title: str = ""
        self.authors: List[str] = []
        self.abstract: str = ""
        self.published_date: Optional[datetime] = None
        self.volume: Optional[str] = None
        self.issue: Optional[str] = None
        self.pages: Optional[str] = None
        self.doi: Optional[str] = None
        self.keywords: List[str] = []
        self.journal_specific: Dict[str, Any] = {}


class DownloadSession:
    """Manages HTTP session for journal downloads with rate limiting."""
    
    def __init__(self, 
                 rate_limit_delay: float = 2.0,
                 request_timeout: int = 30,
                 max_retries: int = 3):
        self.rate_limit_delay = rate_limit_delay
        self.request_timeout = request_timeout
        self.max_retries = max_retries
        self.last_request_time = 0.0
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        timeout = aiohttp.ClientTimeout(total=self.request_timeout)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def get(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Make a rate-limited GET request."""
        if not self.session:
            raise RuntimeError("Session not initialized")
        
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - time_since_last)
        
        # Make request with retries
        for attempt in range(self.max_retries):
            try:
                self.last_request_time = time.time()
                response = await self.session.get(url, **kwargs)
                return response
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff


class BaseJournalHandler(ABC):
    """Abstract base class for journal-specific handlers."""
    
    def __init__(self, 
                 journal_name: str,
                 base_url: str,
                 instance_name: str,
                 rate_limit_delay: float = 2.0):
        """
        Initialize BaseJournalHandler.
        
        Args:
            journal_name: Name of the journal
            base_url: Base URL for the journal website
            instance_name: Name of the scholar instance
            rate_limit_delay: Delay between requests (seconds)
        """
        self.journal_name = journal_name
        self.base_url = base_url
        self.instance_name = instance_name
        self.rate_limit_delay = rate_limit_delay
        
        # Statistics
        self.papers_discovered = 0
        self.papers_downloaded = 0
        self.papers_failed = 0
        
        logger.info(f"BaseJournalHandler initialized for '{journal_name}' "
                   f"in instance '{instance_name}'")
    
    @abstractmethod
    async def discover_papers(self, 
                            start_date: datetime, 
                            end_date: datetime) -> List[JournalPaper]:
        """
        Discover papers from the journal for the given date range.
        
        Args:
            start_date: Start date for paper discovery
            end_date: End date for paper discovery
            
        Returns:
            List of discovered journal papers
        """
        pass
    
    @abstractmethod
    async def download_paper(self, paper: JournalPaper, output_dir: Path) -> Optional[str]:
        """
        Download a specific paper PDF.
        
        Args:
            paper: Journal paper to download
            output_dir: Directory to save the PDF
            
        Returns:
            Path to downloaded PDF file, or None if failed
        """
        pass
    
    @abstractmethod
    async def extract_metadata(self, paper_url: str) -> Optional[JournalMetadata]:
        """
        Extract metadata from a paper's webpage.
        
        Args:
            paper_url: URL of the paper's webpage
            
        Returns:
            JournalMetadata object, or None if extraction failed
        """
        pass
    
    async def download_papers_batch(self, 
                                  papers: List[JournalPaper], 
                                  output_dir: Path,
                                  max_concurrent: int = 3) -> Dict[str, Any]:
        """
        Download multiple papers concurrently.
        
        Args:
            papers: List of papers to download
            output_dir: Directory to save PDFs
            max_concurrent: Maximum concurrent downloads
            
        Returns:
            Dictionary with download statistics
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        semaphore = asyncio.Semaphore(max_concurrent)
        results = {
            'successful': [],
            'failed': [],
            'total_size_mb': 0.0,
            'download_time': 0.0
        }
        
        start_time = time.time()
        
        async def download_single(paper: JournalPaper) -> None:
            async with semaphore:
                try:
                    pdf_path = await self.download_paper(paper, output_dir)
                    if pdf_path:
                        results['successful'].append(pdf_path)
                        # Calculate file size
                        file_size = Path(pdf_path).stat().st_size / (1024**2)  # MB
                        results['total_size_mb'] += file_size
                        self.papers_downloaded += 1
                    else:
                        results['failed'].append(paper.paper_id)
                        self.papers_failed += 1
                except Exception as e:
                    logger.error(f"Failed to download paper {paper.paper_id}: {e}")
                    results['failed'].append(paper.paper_id)
                    self.papers_failed += 1
        
        # Execute downloads
        tasks = [download_single(paper) for paper in papers]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        results['download_time'] = time.time() - start_time
        
        logger.info(f"Batch download completed for {self.journal_name}: "
                   f"{len(results['successful'])} successful, "
                   f"{len(results['failed'])} failed")
        
        return results
    
    def create_journal_paper(self, 
                           paper_id: str,
                           metadata: JournalMetadata,
                           pdf_url: str,
                           journal_url: str) -> JournalPaper:
        """
        Create a JournalPaper object from metadata.
        
        Args:
            paper_id: Unique identifier for the paper
            metadata: Extracted metadata
            pdf_url: URL to the PDF file
            journal_url: URL to the paper's journal page
            
        Returns:
            JournalPaper object
        """
        return JournalPaper(
            paper_id=paper_id,
            title=metadata.title,
            authors=metadata.authors,
            abstract=metadata.abstract,
            published_date=metadata.published_date or datetime.now(),
            source_type='journal',
            instance_name=self.instance_name,
            journal_name=self.journal_name,
            volume=metadata.volume,
            issue=metadata.issue,
            pages=metadata.pages,
            doi=metadata.doi,
            pdf_url=pdf_url,
            journal_url=journal_url,
            metadata={
                'keywords': metadata.keywords,
                'journal_specific': metadata.journal_specific,
                'discovered_date': datetime.now().isoformat()
            }
        )
    
    def get_safe_filename(self, paper: JournalPaper) -> str:
        """
        Generate a safe filename for a paper.
        
        Args:
            paper: Journal paper
            
        Returns:
            Safe filename string
        """
        # Clean title for filename
        safe_title = "".join(c for c in paper.title[:50] if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = safe_title.replace(' ', '_')
        
        # Include volume/issue if available
        vol_issue = ""
        if paper.volume:
            vol_issue += f"_v{paper.volume}"
        if paper.issue:
            vol_issue += f"_i{paper.issue}"
        
        return f"{paper.paper_id}_{safe_title}{vol_issue}.pdf"
    
    async def validate_pdf_download(self, file_path: Path) -> bool:
        """
        Validate that a downloaded file is a valid PDF.
        
        Args:
            file_path: Path to the downloaded file
            
        Returns:
            True if valid PDF, False otherwise
        """
        try:
            if not file_path.exists():
                return False
            
            # Check file size (should be > 1KB)
            if file_path.stat().st_size < 1024:
                return False
            
            # Check PDF header
            with open(file_path, 'rb') as f:
                header = f.read(4)
                if header != b'%PDF':
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating PDF {file_path}: {e}")
            return False
    
    def get_handler_stats(self) -> Dict[str, Any]:
        """
        Get statistics for this journal handler.
        
        Returns:
            Dictionary with handler statistics
        """
        return {
            'journal_name': self.journal_name,
            'instance_name': self.instance_name,
            'base_url': self.base_url,
            'papers_discovered': self.papers_discovered,
            'papers_downloaded': self.papers_downloaded,
            'papers_failed': self.papers_failed,
            'success_rate': (
                self.papers_downloaded / max(self.papers_downloaded + self.papers_failed, 1) * 100
            )
        }
    
    async def test_connection(self) -> bool:
        """
        Test connection to the journal website.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            async with DownloadSession(self.rate_limit_delay) as session:
                response = await session.get(self.base_url)
                return response.status == 200
        except Exception as e:
            logger.error(f"Connection test failed for {self.journal_name}: {e}")
            return False
    
    def reset_stats(self) -> None:
        """Reset handler statistics."""
        self.papers_discovered = 0
        self.papers_downloaded = 0
        self.papers_failed = 0
        logger.info(f"Statistics reset for {self.journal_name} handler")


class JournalHandlerRegistry:
    """Registry for managing multiple journal handlers."""
    
    def __init__(self):
        self.handlers: Dict[str, BaseJournalHandler] = {}
        logger.info("JournalHandlerRegistry initialized")
    
    def register_handler(self, handler: BaseJournalHandler) -> None:
        """
        Register a journal handler.
        
        Args:
            handler: Journal handler to register
        """
        key = f"{handler.instance_name}_{handler.journal_name}"
        self.handlers[key] = handler
        logger.info(f"Registered handler for {handler.journal_name} "
                   f"in instance {handler.instance_name}")
    
    def get_handler(self, instance_name: str, journal_name: str) -> Optional[BaseJournalHandler]:
        """
        Get a journal handler by instance and journal name.
        
        Args:
            instance_name: Name of the scholar instance
            journal_name: Name of the journal
            
        Returns:
            Journal handler if found, None otherwise
        """
        key = f"{instance_name}_{journal_name}"
        return self.handlers.get(key)
    
    def get_handlers_for_instance(self, instance_name: str) -> List[BaseJournalHandler]:
        """
        Get all journal handlers for a specific instance.
        
        Args:
            instance_name: Name of the scholar instance
            
        Returns:
            List of journal handlers for the instance
        """
        return [
            handler for key, handler in self.handlers.items()
            if key.startswith(f"{instance_name}_")
        ]
    
    def list_journals(self, instance_name: Optional[str] = None) -> List[str]:
        """
        List all registered journals.
        
        Args:
            instance_name: Optional instance name to filter by
            
        Returns:
            List of journal names
        """
        if instance_name:
            handlers = self.get_handlers_for_instance(instance_name)
            return [handler.journal_name for handler in handlers]
        else:
            return [handler.journal_name for handler in self.handlers.values()]
    
    async def test_all_connections(self, instance_name: Optional[str] = None) -> Dict[str, bool]:
        """
        Test connections for all registered handlers.
        
        Args:
            instance_name: Optional instance name to filter by
            
        Returns:
            Dictionary mapping journal names to connection status
        """
        results = {}
        
        handlers = (self.get_handlers_for_instance(instance_name) 
                   if instance_name else self.handlers.values())
        
        for handler in handlers:
            try:
                is_connected = await handler.test_connection()
                results[handler.journal_name] = is_connected
            except Exception as e:
                logger.error(f"Connection test failed for {handler.journal_name}: {e}")
                results[handler.journal_name] = False
        
        return results
    
    def get_global_stats(self) -> Dict[str, Any]:
        """
        Get aggregated statistics for all handlers.
        
        Returns:
            Dictionary with global statistics
        """
        total_discovered = sum(h.papers_discovered for h in self.handlers.values())
        total_downloaded = sum(h.papers_downloaded for h in self.handlers.values())
        total_failed = sum(h.papers_failed for h in self.handlers.values())
        
        return {
            'total_handlers': len(self.handlers),
            'total_journals': len(set(h.journal_name for h in self.handlers.values())),
            'total_instances': len(set(h.instance_name for h in self.handlers.values())),
            'total_papers_discovered': total_discovered,
            'total_papers_downloaded': total_downloaded,
            'total_papers_failed': total_failed,
            'overall_success_rate': (
                total_downloaded / max(total_downloaded + total_failed, 1) * 100
            ),
            'handlers': {
                key: handler.get_handler_stats() 
                for key, handler in self.handlers.items()
            }
        }


# Global registry instance
journal_handler_registry = JournalHandlerRegistry()