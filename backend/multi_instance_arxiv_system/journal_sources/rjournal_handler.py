"""
R Journal Handler.

Specialized handler for downloading papers from The R Journal.
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


class RJournalHandler(BaseJournalHandler):
    """Handler for The R Journal."""
    
    def __init__(self, instance_name: str):
        """
        Initialize R Journal handler.
        
        Args:
            instance_name: Name of the scholar instance
        """
        super().__init__(
            instance_name=instance_name,
            base_url="https://journal.r-project.org",
            journal_name="The R Journal"
        )
        
        # R Journal specific configuration
        self.issues_url = f"{self.base_url}/issues.html"
        self.archive_url = f"{self.base_url}/archive"
        
        # Cache for discovered issues
        self._issues_cache: Optional[List[Dict[str, Any]]] = None
        self._cache_timestamp: Optional[datetime] = None
        self._cache_duration = timedelta(hours=1)  # Cache for 1 hour
    
    async def discover_papers(self, 
                            start_date: datetime, 
                            end_date: datetime,
                            max_papers: int = 100) -> List[Dict[str, Any]]:
        """
        Discover papers from The R Journal within the specified date range.
        
        Args:
            start_date: Start date for paper search
            end_date: End date for paper search
            max_papers: Maximum number of papers to discover
            
        Returns:
            List of paper information dictionaries
        """
        logger.info(f"Discovering R Journal papers from {start_date.date()} to {end_date.date()}")
        
        papers = []
        
        try:
            # Get list of issues
            issues = await self._get_issues()
            
            for issue in issues:
                try:
                    # Check if issue is in date range
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
                    logger.error(f"Error processing R Journal issue {issue.get('title', 'unknown')}: {e}")
                    continue
            
            logger.info(f"Discovered {len(papers)} papers from The R Journal")
            return papers
            
        except Exception as e:
            logger.error(f"Error discovering R Journal papers: {e}")
            return []
    
    async def _get_issues(self) -> List[Dict[str, Any]]:
        """Get list of R Journal issues."""
        # Check cache first
        if (self._issues_cache and 
            self._cache_timestamp and 
            datetime.now() - self._cache_timestamp < self._cache_duration):
            return self._issues_cache
        
        logger.info("Fetching R Journal issues list")
        
        try:
            # Try both the issues page and archive
            issues = []
            
            # Get from main issues page
            response = await self.fetch_with_retry(self.issues_url)
            if response:
                content = await response.text()
                issues.extend(self._parse_issues_page(content))
            
            # Get from archive if available
            archive_response = await self.fetch_with_retry(self.archive_url)
            if archive_response:
                archive_content = await archive_response.text()
                issues.extend(self._parse_archive_page(archive_content))
            
            # Remove duplicates and sort
            unique_issues = {}
            for issue in issues:
                key = f"{issue['year']}_{issue['issue']}"
                if key not in unique_issues:
                    unique_issues[key] = issue
            
            issues = list(unique_issues.values())
            issues.sort(key=lambda x: (int(x['year']), int(x['issue'])), reverse=True)
            
            # Update cache
            self._issues_cache = issues
            self._cache_timestamp = datetime.now()
            
            logger.info(f"Found {len(issues)} R Journal issues")
            return issues
            
        except Exception as e:
            logger.error(f"Error fetching R Journal issues: {e}")
            return []
    
    def _parse_issues_page(self, html_content: str) -> List[Dict[str, Any]]:
        """
        Parse the R Journal issues page.
        
        Args:
            html_content: HTML content of the issues page
            
        Returns:
            List of issue information dictionaries
        """
        issues = []
        
        try:
            # Look for issue links in the HTML
            # R Journal uses patterns like "/archive/2023-1/" or "/archive/2023/RJ-2023-1/"
            issue_patterns = [
                r'href="(/archive/(\d{4})-(\d+)/)"[^>]*>([^<]+)</a>',
                r'href="(/archive/(\d{4})/[^"]*(\d+)[^"]*)"[^>]*>([^<]+)</a>'
            ]
            
            for pattern in issue_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                for match in matches:
                    if len(match) == 4:  # First pattern
                        issue_path, year, issue_num, title = match
                    else:  # Second pattern might have different structure
                        continue
                    
                    issue_info = {
                        'path': issue_path,
                        'title': self.clean_text(title),
                        'year': year,
                        'issue': issue_num,
                        'url': urljoin(self.base_url, issue_path)
                    }
                    
                    issues.append(issue_info)
            
        except Exception as e:
            logger.error(f"Error parsing R Journal issues page: {e}")
        
        return issues
    
    def _parse_archive_page(self, html_content: str) -> List[Dict[str, Any]]:
        """
        Parse the R Journal archive page.
        
        Args:
            html_content: HTML content of the archive page
            
        Returns:
            List of issue information dictionaries
        """
        issues = []
        
        try:
            # Look for year/issue patterns in archive
            year_pattern = r'(\d{4})'
            issue_pattern = r'Issue\s+(\d+)'
            
            # Find all years mentioned
            years = re.findall(year_pattern, html_content)
            
            for year in set(years):
                # Look for issues in this year
                year_section = re.search(
                    rf'{year}.*?(?=\d{{4}}|$)', 
                    html_content, 
                    re.DOTALL
                )
                
                if year_section:
                    section_text = year_section.group(0)
                    issue_matches = re.findall(issue_pattern, section_text, re.IGNORECASE)
                    
                    for issue_num in issue_matches:
                        issue_info = {
                            'path': f'/archive/{year}-{issue_num}/',
                            'title': f'The R Journal {year} Issue {issue_num}',
                            'year': year,
                            'issue': issue_num,
                            'url': f"{self.base_url}/archive/{year}-{issue_num}/"
                        }
                        
                        issues.append(issue_info)
            
        except Exception as e:
            logger.error(f"Error parsing R Journal archive page: {e}")
        
        return issues
    
    def _is_issue_in_date_range(self, 
                               issue: Dict[str, Any], 
                               start_date: datetime, 
                               end_date: datetime) -> bool:
        """
        Check if an issue is in the date range.
        
        Args:
            issue: Issue information dictionary
            start_date: Start date
            end_date: End date
            
        Returns:
            True if issue is in range, False otherwise
        """
        try:
            year = int(issue['year'])
            issue_num = int(issue['issue'])
            
            # Estimate publication date (R Journal typically publishes 1-2 issues per year)
            # Issue 1 is usually published mid-year, Issue 2 at end of year
            if issue_num == 1:
                estimated_date = datetime(year, 6, 1)  # June
            else:
                estimated_date = datetime(year, 12, 1)  # December
            
            # Allow some buffer (6 months on each side)
            buffer = timedelta(days=180)
            return (start_date - buffer) <= estimated_date <= (end_date + buffer)
            
        except Exception:
            # If we can't estimate, include it to be safe
            return True
    
    async def _get_papers_from_issue(self, issue: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get papers from a specific R Journal issue.
        
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
            logger.error(f"Error getting papers from R Journal issue {issue['title']}: {e}")
        
        return papers
    
    def _parse_issue_page(self, 
                         html_content: str, 
                         issue: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse an R Journal issue page to extract paper information.
        
        Args:
            html_content: HTML content of the issue page
            issue: Issue information
            
        Returns:
            List of paper information dictionaries
        """
        papers = []
        
        try:
            # Look for article titles and links
            # R Journal often has patterns like:
            # - Links to individual articles
            # - PDF download links
            # - Article titles in headers
            
            article_patterns = [
                r'<h[1-6][^>]*>([^<]+)</h[1-6]>[^<]*<[^>]*href="([^"]+\.pdf)"',
                r'href="([^"]+\.pdf)"[^>]*>([^<]+)</a>',
                r'<a[^>]+href="([^"]+)"[^>]*>([^<]+)</a>[^<]*\.pdf',
            ]
            
            for pattern in article_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE | re.DOTALL)
                
                for match in matches:
                    if len(match) == 2:
                        if match[0].endswith('.pdf'):
                            pdf_url, title = match
                            article_url = pdf_url
                        else:
                            title, pdf_url = match
                            article_url = match[0]
                    else:
                        continue
                    
                    # Clean up title
                    title = self.clean_text(title)
                    
                    # Skip if title is too short or looks like navigation
                    if (len(title) < 5 or 
                        title.lower() in ['pdf', 'download', 'abstract', 'full text']):
                        continue
                    
                    # Make URLs absolute
                    if pdf_url and not pdf_url.startswith('http'):
                        pdf_url = urljoin(self.base_url, pdf_url)
                    if article_url and not article_url.startswith('http'):
                        article_url = urljoin(self.base_url, article_url)
                    
                    paper_info = {
                        'title': title,
                        'url': article_url,
                        'pdf_url': pdf_url,
                        'year': issue['year'],
                        'issue': issue['issue'],
                        'journal': self.journal_name,
                        'source': 'rjournal',
                        'issue_title': issue['title']
                    }
                    
                    papers.append(paper_info)
            
            # Also look for a table of contents or article list
            toc_pattern = r'<table[^>]*>.*?</table>'
            toc_matches = re.findall(toc_pattern, html_content, re.IGNORECASE | re.DOTALL)
            
            for toc in toc_matches:
                # Extract articles from table
                row_pattern = r'<tr[^>]*>(.*?)</tr>'
                rows = re.findall(row_pattern, toc, re.IGNORECASE | re.DOTALL)
                
                for row in rows:
                    # Look for title and PDF link in the row
                    title_match = re.search(r'>([^<]{10,})<', row)
                    pdf_match = re.search(r'href="([^"]+\.pdf)"', row, re.IGNORECASE)
                    
                    if title_match and pdf_match:
                        title = self.clean_text(title_match.group(1))
                        pdf_url = urljoin(self.base_url, pdf_match.group(1))
                        
                        paper_info = {
                            'title': title,
                            'url': pdf_url,
                            'pdf_url': pdf_url,
                            'year': issue['year'],
                            'issue': issue['issue'],
                            'journal': self.journal_name,
                            'source': 'rjournal',
                            'issue_title': issue['title']
                        }
                        
                        papers.append(paper_info)
            
        except Exception as e:
            logger.error(f"Error parsing R Journal issue page: {e}")
        
        return papers
    
    async def extract_metadata(self, paper_url: str) -> Optional[JournalMetadata]:
        """
        Extract metadata from an R Journal paper page.
        
        Args:
            paper_url: URL to the R Journal paper page
            
        Returns:
            JournalMetadata object or None if extraction fails
        """
        try:
            # If it's a direct PDF link, we can't extract much metadata
            if paper_url.endswith('.pdf'):
                return self._create_minimal_metadata_from_url(paper_url)
            
            response = await self.fetch_with_retry(paper_url)
            if not response:
                return None
            
            content = await response.text()
            return self._parse_paper_metadata(content, paper_url)
            
        except Exception as e:
            logger.error(f"Error extracting metadata from {paper_url}: {e}")
            return None
    
    def _create_minimal_metadata_from_url(self, pdf_url: str) -> Optional[JournalMetadata]:
        """
        Create minimal metadata from PDF URL when no paper page is available.
        
        Args:
            pdf_url: URL to the PDF file
            
        Returns:
            JournalMetadata object with minimal information
        """
        try:
            # Extract year and issue from URL
            year_match = re.search(r'(\d{4})', pdf_url)
            issue_match = re.search(r'(\d+)', pdf_url.split('/')[-1])
            
            year = year_match.group(1) if year_match else None
            issue = issue_match.group(1) if issue_match else None
            
            # Create basic title from filename
            filename = Path(pdf_url).stem
            title = filename.replace('_', ' ').replace('-', ' ').title()
            
            metadata = JournalMetadata(
                title=title,
                authors=['Unknown Author'],
                abstract='No abstract available',
                journal_name=self.journal_name,
                volume=year,  # R Journal uses year as volume
                issue=issue,
                url=pdf_url,
                publication_date=datetime(int(year), 1, 1) if year else datetime.now()
            )
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error creating minimal metadata from {pdf_url}: {e}")
            return None
    
    def _parse_paper_metadata(self, 
                            html_content: str, 
                            paper_url: str) -> Optional[JournalMetadata]:
        """
        Parse R Journal paper page to extract metadata.
        
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
                r'<h2[^>]*>([^<]+)</h2>'
            ]
            
            title = None
            for pattern in title_patterns:
                match = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
                if match:
                    title = self.clean_text(match.group(1))
                    # Clean up common title prefixes
                    title = re.sub(r'^(The R Journal|R Journal)[\s:]*', '', title, flags=re.IGNORECASE)
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
            
            # Extract year and issue from URL or content
            year_match = re.search(r'(\d{4})', paper_url)
            issue_match = re.search(r'(\d+)', paper_url)
            
            year = year_match.group(1) if year_match else None
            issue = issue_match.group(1) if issue_match else None
            
            # Extract DOI
            doi = self.extract_doi(html_content)
            
            # Create metadata object
            metadata = JournalMetadata(
                title=title,
                authors=authors,
                abstract=abstract or "No abstract available",
                journal_name=self.journal_name,
                volume=year,  # R Journal uses year as volume
                issue=issue,
                doi=doi,
                url=paper_url,
                publication_date=datetime(int(year), 1, 1) if year else datetime.now()
            )
            
            if self.validate_metadata(metadata):
                return metadata
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error parsing R Journal paper metadata: {e}")
            return None
    
    async def download_paper(self, 
                           paper_info: Dict[str, Any], 
                           download_dir: Path) -> Optional[str]:
        """
        Download an R Journal paper PDF.
        
        Args:
            paper_info: Paper information dictionary
            download_dir: Directory to save the PDF
            
        Returns:
            Path to downloaded file or None if download fails
        """
        try:
            # Generate filename
            year = paper_info.get('year', 'unknown')
            issue = paper_info.get('issue', 'unknown')
            
            # Create safe filename
            title_part = re.sub(r'[^\w\s-]', '', paper_info['title'])[:50]
            title_part = re.sub(r'\s+', '_', title_part.strip())
            
            filename = f"rjournal_{year}_{issue}_{title_part}.pdf"
            file_path = download_dir / filename
            
            # Skip if already exists
            if file_path.exists() and file_path.stat().st_size > 1024:
                logger.debug(f"R Journal paper already exists: {filename}")
                return str(file_path)
            
            # Get PDF URL
            pdf_url = paper_info.get('pdf_url') or paper_info.get('url')
            if not pdf_url:
                logger.error(f"No PDF URL found for {paper_info['title']}")
                return None
            
            # If URL doesn't end with .pdf, try to find the PDF link
            if not pdf_url.endswith('.pdf'):
                pdf_url = await self._find_pdf_url(pdf_url)
                if not pdf_url:
                    logger.error(f"Could not find PDF URL for {paper_info['title']}")
                    return None
            
            # Download the PDF
            success = await self.download_pdf_from_url(pdf_url, file_path)
            
            if success:
                logger.info(f"Downloaded R Journal paper: {filename}")
                return str(file_path)
            else:
                logger.error(f"Failed to download R Journal paper: {paper_info['title']}")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading R Journal paper {paper_info.get('title', 'unknown')}: {e}")
            return None
    
    async def _find_pdf_url(self, paper_url: str) -> Optional[str]:
        """
        Find the PDF download URL for an R Journal paper.
        
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
                    if '.pdf' in pdf_url.lower():
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
            pub_date = metadata.publication_date
        else:
            # Use basic info from paper_info
            paper_id = f"rjournal_{paper_info.get('year', 'unknown')}_{paper_info.get('issue', 'unknown')}"
            title = paper_info.get('title', 'Unknown Title')
            authors = ['Unknown Author']
            abstract = 'No abstract available'
            volume = paper_info.get('year')
            issue = paper_info.get('issue')
            doi = None
            pub_date = datetime.now()
        
        return JournalPaper(
            paper_id=paper_id,
            title=title,
            authors=authors,
            abstract=abstract,
            published_date=pub_date,
            source_type='journal',
            instance_name=self.instance_name,
            journal_name=self.journal_name,
            volume=volume,
            issue=issue,
            doi=doi,
            pdf_url=paper_info.get('pdf_url', paper_info.get('url', '')),
            journal_url=paper_info.get('url', ''),
            metadata={
                'source': 'rjournal',
                'discovered_at': datetime.now().isoformat(),
                'handler': 'RJournalHandler'
            }
        )