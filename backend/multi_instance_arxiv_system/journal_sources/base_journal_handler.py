"""
Base Journal Handler for multi-instance ArXiv system.

Provides abstract base class and common functionality for journal source handlers.
"""

import asyncio
import logging
import aiohttp
import aiofiles
from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import re
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class JournalMetadata:
    """Metadata extracted from journal papers."""
    title: str
    authors: List[str]
    abstract: str
    journal_name: str
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    doi: Optional[str] = None
    publication_date: Optional[datetime] = None
    keywords: List[str] = None
    url: Optional[str] = None
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []


class BaseJournalHandler(ABC):
    """Abstract base class for journal source handlers."""
    
    def __init__(self, instance_name: str, base_url: str, journal_name: str):
        """
        Initialize journal handler.
        
        Args:
            instance_name: Name of the scholar instance
            base_url: Base URL of the journal website
            journal_name: Full name of the journal
        """
        self.instance_name = instance_name
        self.base_url = base_url
        self.journal_name = journal_name
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Request configuration
        self.timeout = aiohttp.ClientTimeout(total=300)  # 5 minutes
        self.max_retries = 3
        self.retry_delay = 2.0
        
        logger.info(f"Initialized {self.__class__.__name__} for '{journal_name}'")
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=self.timeout,
            connector=aiohttp.TCPConnector(limit=5),
            headers={
                'User-Agent': 'Mozilla/5.0 (compatible; ScholarBot/1.0; +https://example.com/bot)'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    @abstractmethod
    async def discover_papers(self, 
                            start_date: datetime, 
                            end_date: datetime,
                            max_papers: int = 100) -> List[Dict[str, Any]]:
        """
        Discover papers from this journal source.
        
        Args:
            start_date: Start date for paper search
            end_date: End date for paper search
            max_papers: Maximum number of papers to discover
            
        Returns:
            List of paper metadata dictionaries
        """
        pass
    
    @abstractmethod
    async def extract_metadata(self, paper_url: str) -> Optional[JournalMetadata]:
        """
        Extract metadata from a paper URL.
        
        Args:
            paper_url: URL to the paper page
            
        Returns:
            JournalMetadata object or None if extraction fails
        """
        pass
    
    @abstractmethod
    async def download_paper(self, 
                           paper_info: Dict[str, Any], 
                           download_dir: Path) -> Optional[str]:
        """
        Download a specific paper PDF.
        
        Args:
            paper_info: Paper information dictionary
            download_dir: Directory to save the PDF
            
        Returns:
            Path to downloaded file or None if download fails
        """
        pass
    
    async def fetch_with_retry(self, url: str, **kwargs) -> Optional[aiohttp.ClientResponse]:
        """
        Fetch URL with retry logic.
        
        Args:
            url: URL to fetch
            **kwargs: Additional arguments for aiohttp request
            
        Returns:
            Response object or None if all retries fail
        """
        if not self.session:
            raise RuntimeError("Session not initialized - use async context manager")
        
        for attempt in range(self.max_retries):
            try:
                async with self.session.get(url, **kwargs) as response:
                    if response.status == 200:
                        return response
                    elif response.status == 429:  # Rate limited
                        wait_time = self.retry_delay * (2 ** attempt)
                        logger.warning(f"Rate limited, waiting {wait_time}s before retry")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.warning(f"HTTP {response.status} for {url}")
                        
            except asyncio.TimeoutError:
                logger.warning(f"Timeout for {url}, attempt {attempt + 1}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
            except Exception as e:
                logger.error(f"Error fetching {url}: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
        
        logger.error(f"Failed to fetch {url} after {self.max_retries} attempts")
        return None
    
    async def download_pdf_from_url(self, 
                                  pdf_url: str, 
                                  file_path: Path,
                                  expected_size: Optional[int] = None) -> bool:
        """
        Download PDF from URL with validation.
        
        Args:
            pdf_url: URL to the PDF file
            file_path: Path to save the PDF
            expected_size: Expected file size in bytes (optional)
            
        Returns:
            True if download successful, False otherwise
        """
        try:
            # Skip if file already exists and has reasonable size
            if file_path.exists():
                existing_size = file_path.stat().st_size
                if existing_size > 1024:  # At least 1KB
                    logger.debug(f"PDF already exists: {file_path}")
                    return True
            
            # Create directory if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Download with retry
            response = await self.fetch_with_retry(pdf_url)
            if not response:
                return False
            
            # Check content type
            content_type = response.headers.get('content-type', '').lower()
            if 'pdf' not in content_type and 'application/octet-stream' not in content_type:
                logger.warning(f"Unexpected content type for {pdf_url}: {content_type}")
            
            # Download to temporary file first
            temp_path = file_path.with_suffix('.tmp')
            
            async with aiofiles.open(temp_path, 'wb') as f:
                async for chunk in response.content.iter_chunked(8192):
                    await f.write(chunk)
            
            # Validate downloaded file
            file_size = temp_path.stat().st_size
            
            # Check minimum size
            if file_size < 1024:  # Less than 1KB is suspicious
                logger.error(f"Downloaded file too small: {file_size} bytes")
                temp_path.unlink()
                return False
            
            # Check expected size if provided
            if expected_size and abs(file_size - expected_size) > expected_size * 0.1:
                logger.warning(f"File size mismatch: expected ~{expected_size}, got {file_size}")
            
            # Validate PDF header
            with open(temp_path, 'rb') as f:
                header = f.read(4)
                if header != b'%PDF':
                    logger.error(f"Invalid PDF header: {header}")
                    temp_path.unlink()
                    return False
            
            # Move to final location
            temp_path.rename(file_path)
            
            logger.info(f"Successfully downloaded PDF: {file_path.name} ({file_size} bytes)")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading PDF from {pdf_url}: {e}")
            # Clean up temporary file if it exists
            temp_path = file_path.with_suffix('.tmp')
            if temp_path.exists():
                temp_path.unlink()
            return False
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text content.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove common HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        
        return text
    
    def extract_doi(self, text: str) -> Optional[str]:
        """
        Extract DOI from text.
        
        Args:
            text: Text that may contain a DOI
            
        Returns:
            DOI string or None if not found
        """
        # Common DOI patterns
        doi_patterns = [
            r'doi:\s*([0-9]+\.[0-9]+/[^\s]+)',
            r'DOI:\s*([0-9]+\.[0-9]+/[^\s]+)',
            r'https?://doi\.org/([0-9]+\.[0-9]+/[^\s]+)',
            r'https?://dx\.doi\.org/([0-9]+\.[0-9]+/[^\s]+)'
        ]
        
        for pattern in doi_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def parse_authors(self, author_text: str) -> List[str]:
        """
        Parse author names from text.
        
        Args:
            author_text: Text containing author names
            
        Returns:
            List of author names
        """
        if not author_text:
            return []
        
        # Clean the text
        author_text = self.clean_text(author_text)
        
        # Common separators
        separators = [',', ';', ' and ', ' & ', '\n']
        
        authors = [author_text]
        for sep in separators:
            new_authors = []
            for author in authors:
                new_authors.extend([a.strip() for a in author.split(sep) if a.strip()])
            authors = new_authors
        
        # Filter out empty strings and common non-author text
        filtered_authors = []
        for author in authors:
            author = author.strip()
            if (author and 
                len(author) > 2 and 
                not author.lower().startswith('email') and
                not author.lower().startswith('affiliation')):
                filtered_authors.append(author)
        
        return filtered_authors[:10]  # Limit to reasonable number
    
    def generate_paper_id(self, metadata: JournalMetadata) -> str:
        """
        Generate a unique paper ID for the journal paper.
        
        Args:
            metadata: Paper metadata
            
        Returns:
            Unique paper ID
        """
        # Create a hash from title and journal info
        content = f"{metadata.title}_{metadata.journal_name}_{metadata.volume}_{metadata.issue}"
        hash_obj = hashlib.md5(content.encode('utf-8'))
        hash_str = hash_obj.hexdigest()[:8]
        
        # Create readable ID
        journal_prefix = self.journal_name.lower().replace(' ', '_').replace('.', '')[:10]
        
        if metadata.volume and metadata.issue:
            return f"{journal_prefix}_v{metadata.volume}i{metadata.issue}_{hash_str}"
        else:
            return f"{journal_prefix}_{hash_str}"
    
    def validate_metadata(self, metadata: JournalMetadata) -> bool:
        """
        Validate extracted metadata.
        
        Args:
            metadata: Metadata to validate
            
        Returns:
            True if metadata is valid, False otherwise
        """
        # Check required fields
        if not metadata.title or len(metadata.title.strip()) < 5:
            logger.warning("Invalid or missing title")
            return False
        
        if not metadata.authors:
            logger.warning("No authors found")
            return False
        
        if not metadata.journal_name:
            logger.warning("Missing journal name")
            return False
        
        # Check for reasonable content
        if len(metadata.title) > 500:
            logger.warning("Title too long, might be corrupted")
            return False
        
        return True
    
    def get_handler_stats(self) -> Dict[str, Any]:
        """
        Get statistics for this handler.
        
        Returns:
            Dictionary with handler statistics
        """
        return {
            'handler_type': self.__class__.__name__,
            'journal_name': self.journal_name,
            'base_url': self.base_url,
            'instance_name': self.instance_name,
            'max_retries': self.max_retries,
            'timeout_seconds': self.timeout.total if self.timeout else None
        }