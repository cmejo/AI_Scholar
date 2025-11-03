"""
Journal of Statistical Software (JSS) Handler.

Specialized handler for downloading papers from the Journal of Statistical Software.
"""

import asyncio
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse
import json

from .base_journal_handler import BaseJournalHandler, JournalMetadata
from ..shared.multi_instance_data_models import JournalPaper

logger = logging.getLogger(__name__)


class JStatSoftwareHandler(BaseJournalHandler):
    """Handler for Journal of Statistical Software."""
    
    def __init__(self, instance_name: str):
        """
        Initialize JSS handler.
        
        Args:
            instance_name: Name of the scholar instance
        """
        super().__init__(
            instance_name=instance_name,
            base_url="https://www.jstatsoft.org",
            journal_name="Journal of Statistical Software"
        )
        
        # JSS specific configuration
        self.issues_url = f"{self.base_url}/issue/archive"
        self.article_base_url = f"{self.base_url}/article/view"
        
        # Cache for discovered issues
        self._issues_cache: Optional[List[Dict[str, Any]]] = None
        self._cache_timestamp: Optional[datetime] = None
        self._cache_duration = timedelta(hours=1)  # Cache for 1 hour
    
    async def discover_papers(self, 
                            start_date: datetime, 
                            end_date: datetime,
                            max_papers: int = 100) -> List[Dict[str, Any]]:
        """
        Discover papers from JSS within the specified date range.
        
        Args:
            start_date: Start date for paper search
            end_date: End date for paper search
            max_papers: Maximum number of papers to discover
            
        Returns:
            List of paper information dictionaries
        """
        logger.info(f"Discovering JSS papers from {start_date.date()} to {end_date.date()}")
        
        papers = []
        
        try:
            # Get list of issues
            issues = await self._get_issues()
            
            for issue in issues:
                try:
                    # Check if issue is in date range (approximate)
                    if not self._is_issue_in_date_range(issue, start_date, end_date):
                        continue
                    
                    # Get papers from this issue
                    issue_papers = await self._get_papers_from_issue(issue)
                    papers.extend(issue_papers)
                    
                    # Respect rate limiting
                    await asyncio.sleep(1.0)
                    
                    # Check if we have enough papers
                    if len(papers) >= max_papers:
                        papers = papers[:max_papers]
                        break
                        
                except Exception as e:
                    logger.error(f"Error processing JSS issue {issue.get('title', 'unknown')}: {e}")
                    continue
            
            logger.info(f"Discovered {len(papers)} papers from JSS")
            return papers
            
        except Exception as e:
            logger.error(f"Error discovering JSS papers: {e}")
            return []
    
    async def _get_issues(self) -> List[Dict[str, Any]]:
        """Get list of JSS issues."""
        # Check cache first
        if (self._issues_cache and 
            self._cache_timestamp and 
            datetime.now() - self._cache_timestamp < self._cache_duration):
            return self._issues_cache
        
        logger.info("Fetching JSS issues list")
        
        try:
            response = await self.fetch_with_retry(self.issues_url)
            if not response:
                return []
            
            content = await response.text()
            issues = self._parse_issues_page(content)
            
            # Update cache
            self._issues_cache = issues
            self._cache_timestamp = datetime.now()
            
            logger.info(f"Found {len(issues)} JSS issues")
            return issues
            
        except Exception as e:
            logger.error(f"Error fetching JSS issues: {e}")
            return []
    
    def _parse_issues_page(self, html_content: str) -> List[Dict[str, Any]]:
        """
        Parse the JSS issues archive page.
        
        Args:
            html_content: HTML content of the issues page
            
        Returns:
            List of issue information dictionaries
        """
        issues = []
        
        try:
            # Look for issue links in the HTML
            # JSS uses patterns like "/issue/view/v001" or "/issue/view/v050i01"
            issue_pattern = r'href="(/issue/view/v\d+(?:i\d+)?)"[^>]*>([^<]+)</a>'
            matches = re.findall(issue_pattern, html_content, re.IGNORECASE)
            
            for issue_path, issue_title in matches:
                # Extract volume and issue numbers
                volume_match = re.search(r'v(\d+)', issue_path)
                issue_match = re.search(r'i(\d+)', issue_path)
                
                volume = volume_match.group(1) if volume_match else None
                issue_num = issue_match.group(1) if issue_match else None
                
                issue_info = {
                    'path': issue_path,
                    'title': self.clean_text(issue_title),
                    'volume': volume,
                    'issue': issue_num,
                    'url': urljoin(self.base_url, issue_path)
                }
                
                issues.append(issue_info)
            
            # Sort by volume and issue (newest first)
            issues.sort(key=lambda x: (
                int(x['volume']) if x['volume'] else 0,
                int(x['issue']) if x['issue'] else 0
            ), reverse=True)
            
        except Exception as e:
            logger.error(f"Error parsing JSS issues page: {e}")
        
        return issues
    
    def _is_issue_in_date_range(self, 
                               issue: Dict[str, Any], 
                               start_date: datetime, 
                               end_date: datetime) -> bool:
        """
        Check if an issue is likely to be in the date range.
        
        This is approximate since we don't have exact publication dates.
        """
        try:
            volume = int(issue['volume']) if issue['volume'] else 0
            
            # Rough estimation: JSS has been publishing since ~2000
            # Assume roughly 4-6 volumes per year
            estimated_year = 2000 + (volume // 5)
            
            # Create approximate date
            estimated_date = datetime(estimated_year, 6, 1)  # Mid-year
            
            # Allow some buffer (1 year on each side)
            buffer = timedelta(days=365)
            return (start_date - buffer) <= estimated_date <= (end_date + buffer)
            
        except Exception:
            # If we can't estimate, include it to be safe
            return True
    
    async def _get_papers_from_issue(self, issue: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get papers from a specific JSS issue.
        
        Args:
            issue: Issue information dictionary
            
        Returns:
            List of paper information dictionaries
        """
        papers = []
        
        try:
            response = await self.fetch_with_retry(issue['url'])
            if not response:
                return papers
            
            content = await response.text()
            papers = self._parse_issue_page(content, issue)
            
        except Exception as e:
            logger.error(f"Error getting papers from JSS issue {issue['title']}: {e}")
        
        return papers
    
    def _parse_issue_page(self, 
                         html_content: str, 
                         issue: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse a JSS issue page to extract paper information.
        
        Args:
            html_content: HTML content of the issue page
            issue: Issue information
            
        Returns:
            List of paper information dictionaries
        """
        papers = []
        
        try:
            # Look for article links
            # JSS uses patterns like "/article/view/v050i01/paper_title"
            article_pattern = r'href="(/article/view/[^"]+)"[^>]*>([^<]+)</a>'
            matches = re.findall(article_pattern, html_content, re.IGNORECASE)
            
            for article_path, article_title in matches:
                # Skip if it's not a real article (e.g., navigation links)
                if 'view' not in article_path or len(article_title.strip()) < 5:
                    continue
                
                paper_info = {
                    'title': self.clean_text(article_title),
                    'url': urljoin(self.base_url, article_path),
                    'volume': issue['volume'],
                    'issue': issue['issue'],
                    'journal': self.journal_name,
                    'source': 'jss',
                    'issue_title': issue['title']
                }
                
                papers.append(paper_info)
            
        except Exception as e:
            logger.error(f"Error parsing JSS issue page: {e}")
        
        return papers
    
    async def extract_metadata(self, paper_url: str) -> Optional[JournalMetadata]:
        """
        Extract metadata from a JSS paper page.
        
        Args:
            paper_url: URL to the JSS paper page
            
        Returns:
            JournalMetadata object or None if extraction fails
        """
        try:
            response = await self.fetch_with_retry(paper_url)
            if not response:
                return None
            
            content = await response.text()
            return self._parse_paper_metadata(content, paper_url)
            
        except Exception as e:
            logger.error(f"Error extracting metadata from {paper_url}: {e}")
            return None
    
    def _parse_paper_metadata(self, 
                            html_content: str, 
                            paper_url: str) -> Optional[JournalMetadata]:
        """
        Parse JSS paper page to extract metadata.
        
        Args:
            html_content: HTML content of the paper page
            paper_url: URL of the paper page
            
        Returns:
            JournalMetadata object or None if parsing fails
        """
        try:
            # Extract title
            title_patterns = [
                r'<h1[^>]*>([^<]+)</h1>',
                r'<title>([^<]+)</title>',
                r'<h2[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)</h2>'
            ]
            
            title = None
            for pattern in title_patterns:
                match = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
                if match:
                    title = self.clean_text(match.group(1))
                    # Clean up common title prefixes
                    title = re.sub(r'^(JSS|Journal of Statistical Software)[\s:]*', '', title, flags=re.IGNORECASE)
                    break
            
            if not title:
                logger.warning(f"Could not extract title from {paper_url}")
                return None
            
            # Extract authors
            author_patterns = [
                r'<div[^>]*class="[^"]*author[^"]*"[^>]*>([^<]+)</div>',
                r'<span[^>]*class="[^"]*author[^"]*"[^>]*>([^<]+)</span>',
                r'<p[^>]*class="[^"]*author[^"]*"[^>]*>([^<]+)</p>',
                r'Authors?:\s*([^<\n]+)',
                r'By:\s*([^<\n]+)'
            ]
            
            authors = []
            for pattern in author_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE | re.DOTALL)
                for match in matches:
                    parsed_authors = self.parse_authors(match)
                    authors.extend(parsed_authors)
            
            if not authors:
                authors = ['Unknown Author']
            
            # Extract abstract
            abstract_patterns = [
                r'<div[^>]*class="[^"]*abstract[^"]*"[^>]*>([^<]+)</div>',
                r'<p[^>]*class="[^"]*abstract[^"]*"[^>]*>([^<]+)</p>',
                r'Abstract[:\s]*([^<\n]{50,500})',
                r'Summary[:\s]*([^<\n]{50,500})'
            ]
            
            abstract = ""
            for pattern in abstract_patterns:
                match = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
                if match:
                    abstract = self.clean_text(match.group(1))[:2000]  # Limit length
                    break
            
            # Extract volume and issue from URL or content
            volume_match = re.search(r'v(\d+)', paper_url)
            issue_match = re.search(r'i(\d+)', paper_url)
            
            volume = volume_match.group(1) if volume_match else None
            issue = issue_match.group(1) if issue_match else None
            
            # Extract DOI
            doi = self.extract_doi(html_content)
            
            # Create metadata object
            metadata = JournalMetadata(
                title=title,
                authors=authors,
                abstract=abstract or "No abstract available",
                journal_name=self.journal_name,
                volume=volume,
                issue=issue,
                doi=doi,
                url=paper_url,
                publication_date=datetime.now()  # Approximate
            )
            
            if self.validate_metadata(metadata):
                return metadata
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error parsing JSS paper metadata: {e}")
            return None
    
    async def download_paper(self, 
                           paper_info: Dict[str, Any], 
                           download_dir: Path) -> Optional[str]:
        """
        Download a JSS paper PDF.
        
        Args:
            paper_info: Paper information dictionary
            download_dir: Directory to save the PDF
            
        Returns:
            Path to downloaded file or None if download fails
        """
        try:
            # Generate filename
            volume = paper_info.get('volume', 'unknown')
            issue = paper_info.get('issue', 'unknown')
            
            # Create safe filename
            title_part = re.sub(r'[^\w\s-]', '', paper_info['title'])[:50]
            title_part = re.sub(r'\s+', '_', title_part.strip())
            
            filename = f"jss_v{volume}i{issue}_{title_part}.pdf"
            file_path = download_dir / filename
            
            # Skip if already exists
            if file_path.exists() and file_path.stat().st_size > 1024:
                logger.debug(f"JSS paper already exists: {filename}")
                return str(file_path)
            
            # Try to find PDF URL
            pdf_url = await self._find_pdf_url(paper_info['url'])
            if not pdf_url:
                logger.error(f"Could not find PDF URL for {paper_info['title']}")
                return None
            
            # Download the PDF
            success = await self.download_pdf_from_url(pdf_url, file_path)
            
            if success:
                logger.info(f"Downloaded JSS paper: {filename}")
                return str(file_path)
            else:
                logger.error(f"Failed to download JSS paper: {paper_info['title']}")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading JSS paper {paper_info.get('title', 'unknown')}: {e}")
            return None
    
    async def _find_pdf_url(self, paper_url: str) -> Optional[str]:
        """
        Find the PDF download URL for a JSS paper.
        
        Args:
            paper_url: URL of the paper page
            
        Returns:
            PDF URL or None if not found
        """
        try:
            response = await self.fetch_with_retry(paper_url)
            if not response:
                return None
            
            content = await response.text()
            
            # Look for PDF download links
            pdf_patterns = [
                r'href="([^"]*\.pdf)"',
                r'href="([^"]*download[^"]*pdf[^"]*)"',
                r'href="([^"]*pdf[^"]*download[^"]*)"'
            ]
            
            for pattern in pdf_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    # Convert relative URLs to absolute
                    pdf_url = urljoin(self.base_url, match)
                    
                    # Validate that it looks like a PDF URL
                    if '.pdf' in pdf_url.lower() or 'download' in pdf_url.lower():
                        return pdf_url
            
            # If no direct PDF link found, try constructing one
            # JSS often uses patterns like /article/download/v050i01/paper.pdf
            url_parts = paper_url.split('/')
            if 'view' in url_parts:
                view_index = url_parts.index('view')
                if view_index + 1 < len(url_parts):
                    article_id = url_parts[view_index + 1]
                    pdf_url = f"{self.base_url}/article/download/{article_id}/{article_id}.pdf"
                    return pdf_url
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding PDF URL for {paper_url}: {e}")
            return None
    
    def create_journal_paper(self, 
                           paper_info: Dict[str, Any], 
                           metadata: Optional[JournalMetadata] = None) -> JournalPaper:
        """
        Create a JournalPaper object from paper information.
        
        Args:
            paper_info: Paper information dictionary
            metadata: Optional extracted metadata
            
        Returns:
            JournalPaper object
        """
        if metadata:
            paper_id = self.generate_paper_id(metadata)
            title = metadata.title
            authors = metadata.authors
            abstract = metadata.abstract
            volume = metadata.volume
            issue = metadata.issue
            doi = metadata.doi
        else:
            # Use basic info from paper_info
            paper_id = f"jss_{paper_info.get('volume', 'unknown')}_{paper_info.get('issue', 'unknown')}"
            title = paper_info.get('title', 'Unknown Title')
            authors = ['Unknown Author']
            abstract = 'No abstract available'
            volume = paper_info.get('volume')
            issue = paper_info.get('issue')
            doi = None
        
        return JournalPaper(
            paper_id=paper_id,
            title=title,
            authors=authors,
            abstract=abstract,
            published_date=datetime.now(),  # Approximate
            source_type='journal',
            instance_name=self.instance_name,
            journal_name=self.journal_name,
            volume=volume,
            issue=issue,
            doi=doi,
            pdf_url=paper_info.get('url', ''),
            journal_url=paper_info.get('url', ''),
            metadata={
                'source': 'jss',
                'discovered_at': datetime.now().isoformat(),
                'handler': 'JStatSoftwareHandler'
            }
        )