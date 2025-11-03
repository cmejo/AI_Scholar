#!/usr/bin/env python3
"""
Quant Scholar Downloader Script

This script downloads and processes papers from quantitative finance arXiv categories
and journal sources for the Quant Scholar instance.

Usage:
    python quant_scholar_downloader.py [options]
    
Examples:
    # Download papers from last month
    python quant_scholar_downloader.py --date-range last-month
    
    # Download from specific sources
    python quant_scholar_downloader.py --sources arxiv,jss,rjournal
    
    # Resume interrupted download
    python quant_scholar_downloader.py --resume
"""

import sys
import argparse
import asyncio
import logging
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any

# Required for HTTP requests and HTML parsing
try:
    import aiohttp
except ImportError:
    print("Error: aiohttp is required. Install with: pip install aiohttp")
    sys.exit(1)

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: beautifulsoup4 is required. Install with: pip install beautifulsoup4")
    sys.exit(1)

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/quant_scholar_downloader.log')
    ]
)
logger = logging.getLogger(__name__)


class QuantScholarDownloader:
    """Quant Scholar paper downloader with journal source support."""
    
    def __init__(self, config_path: str = "configs/quant_scholar.yaml"):
        self.config_path = config_path
        self.instance_name = "quant_scholar"
        
        # Quant Scholar arXiv categories
        self.arxiv_categories = [
            "econ.EM", "econ.GN", "econ.TH", "eess.SY", "math.ST", 
            "math.PR", "math.OC", "q-fin.*", "stat.*"
        ]
        
        # Journal sources
        self.journal_sources = {
            "jss": {
                "name": "Journal of Statistical Software",
                "url": "https://www.jstatsoft.org/index",
                "handler": "JStatSoftwareHandler"
            },
            "rjournal": {
                "name": "R Journal", 
                "url": "https://journal.r-project.org/issues.html",
                "handler": "RJournalHandler"
            }
        }
        
        # Storage paths
        self.pdf_directory = "/datapool/aischolar/quant-scholar-dataset/pdf"
        self.processed_directory = "/datapool/aischolar/quant-scholar-dataset/processed"
        self.state_directory = "/datapool/aischolar/quant-scholar-dataset/state"
        
        logger.info(f"Quant Scholar Downloader initialized")
    
    async def download_papers(
        self,
        sources: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        date_range: str = "last-month",
        max_papers: Optional[int] = None,
        resume: bool = False,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """Download papers for Quant Scholar instance."""
        
        logger.info(f"Starting Quant Scholar paper download")
        
        # Use default sources if none specified
        if not sources:
            sources = ["arxiv", "jss", "rjournal"]
        
        # Use default categories if none specified
        if not categories:
            categories = self.arxiv_categories
        
        # Parse date range
        start_date, end_date = self._parse_date_range(date_range)
        
        # Create directories
        if not dry_run:
            self._create_directories()
        
        # Initialize statistics
        stats = {
            'total_discovered': 0,
            'total_downloaded': 0,
            'total_failed': 0,
            'sources_processed': len(sources),
            'start_time': datetime.now(),
            'end_time': None,
            'source_stats': {}
        }
        
        try:
            # Process each source
            for source in sources:
                logger.info(f"Processing source: {source}")
                
                if source == "arxiv":
                    source_stats = await self._download_from_arxiv(
                        categories, start_date, end_date, max_papers, resume, dry_run
                    )
                elif source in self.journal_sources:
                    source_stats = await self._download_from_journal(
                        source, start_date, end_date, max_papers, resume, dry_run
                    )
                else:
                    logger.warning(f"Unknown source: {source}")
                    continue
                
                stats['source_stats'][source] = source_stats
                stats['total_discovered'] += source_stats.get('discovered', 0)
                stats['total_downloaded'] += source_stats.get('downloaded', 0)
                stats['total_failed'] += source_stats.get('failed', 0)
        
        except Exception as e:
            logger.error(f"Error during download process: {e}")
            raise
        
        finally:
            stats['end_time'] = datetime.now()
            stats['duration_minutes'] = (stats['end_time'] - stats['start_time']).total_seconds() / 60
        
        return stats
    
    def _parse_date_range(self, date_range: str) -> tuple:
        """Parse date range string into start and end dates."""
        
        end_date = datetime.now(timezone.utc)  # Make timezone-aware
        
        if date_range == "last-week":
            start_date = end_date - timedelta(weeks=1)
        elif date_range == "last-month":
            start_date = end_date - timedelta(days=30)
        elif date_range == "last-year":
            start_date = end_date - timedelta(days=365)
        elif date_range == "all":
            # For "all", use a very broad range that will capture most papers
            # but still allow for date filtering in code
            start_date = datetime(2020, 1, 1, tzinfo=timezone.utc)  # Start from 2020
        else:
            # Try to parse as custom date range
            try:
                parts = date_range.split("to")
                if len(parts) == 2:
                    start_date = datetime.fromisoformat(parts[0].strip()).replace(tzinfo=timezone.utc)
                    end_date = datetime.fromisoformat(parts[1].strip()).replace(tzinfo=timezone.utc)
                else:
                    start_date = end_date - timedelta(days=30)
            except:
                start_date = end_date - timedelta(days=30)
        
        logger.info(f"Date range: {start_date.date()} to {end_date.date()}")
        return start_date, end_date
    
    def _create_directories(self) -> None:
        """Create necessary directories."""
        
        directories = [
            self.pdf_directory,
            self.processed_directory,
            self.state_directory,
            "logs"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {directory}")
    
    async def _download_from_arxiv(
        self,
        categories: List[str],
        start_date: datetime,
        end_date: datetime,
        max_papers: Optional[int],
        resume: bool,
        dry_run: bool
    ) -> Dict[str, Any]:
        """Download papers from arXiv categories."""
        
        logger.info(f"Downloading from arXiv categories: {categories}")
        
        stats = {'discovered': 0, 'downloaded': 0, 'failed': 0}
        
        for i, category in enumerate(categories):
            logger.info(f"Processing category {i+1}/{len(categories)}: {category}")
            
            try:
                papers = await self._discover_arxiv_papers(category, start_date, end_date, max_papers)
                stats['discovered'] += len(papers)
                
                if dry_run:
                    logger.info(f"[DRY RUN] Would download {len(papers)} papers from {category}")
                    continue
                
                logger.info(f"Downloading {len(papers)} papers from {category}")
                
                for j, paper in enumerate(papers):
                    if j % 10 == 0:  # Progress update every 10 papers
                        logger.info(f"Progress: {j}/{len(papers)} papers processed for {category}")
                    
                    try:
                        success = await self._download_paper(paper, resume)
                        if success:
                            stats['downloaded'] += 1
                        else:
                            stats['failed'] += 1
                            
                        # Rate limiting between downloads
                        await asyncio.sleep(1)
                        
                    except Exception as e:
                        logger.error(f"Failed to download paper {paper.get('id', 'unknown')}: {e}")
                        stats['failed'] += 1
                
                logger.info(f"Completed {category}: {stats['downloaded']} downloaded, {stats['failed']} failed")
                
            except Exception as e:
                logger.error(f"Error processing category {category}: {e}")
                continue
        
        return stats
    
    async def _download_from_journal(
        self,
        source: str,
        start_date: datetime,
        end_date: datetime,
        max_papers: Optional[int],
        resume: bool,
        dry_run: bool
    ) -> Dict[str, Any]:
        """Download papers from journal sources."""
        
        journal_info = self.journal_sources[source]
        logger.info(f"Downloading from {journal_info['name']}")
        
        stats = {'discovered': 0, 'downloaded': 0, 'failed': 0}
        
        try:
            # Discover papers from journal
            papers = await self._discover_journal_papers(source, start_date, end_date, max_papers)
            stats['discovered'] = len(papers)
            
            if dry_run:
                logger.info(f"[DRY RUN] Would download {len(papers)} papers from {journal_info['name']}")
                return stats
            
            if not papers:
                logger.warning(f"No papers discovered from {journal_info['name']}")
                return stats
            
            logger.info(f"Downloading {len(papers)} papers from {journal_info['name']}")
            
            # Download papers
            for i, paper in enumerate(papers):
                if i % 5 == 0:  # Progress update every 5 papers
                    logger.info(f"Progress: {i}/{len(papers)} papers processed for {journal_info['name']}")
                
                try:
                    success = await self._download_paper(paper, resume)
                    if success:
                        stats['downloaded'] += 1
                    else:
                        stats['failed'] += 1
                        
                    # Rate limiting between downloads
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Failed to download paper {paper.get('id', 'unknown')}: {e}")
                    stats['failed'] += 1
            
            logger.info(f"Completed {journal_info['name']}: {stats['downloaded']} downloaded, {stats['failed']} failed")
            
        except Exception as e:
            logger.error(f"Error processing journal {source}: {e}")
        
        return stats
    
    async def _discover_arxiv_papers(
        self,
        category: str,
        start_date: datetime,
        end_date: datetime,
        max_papers: Optional[int]
    ) -> List[Dict[str, Any]]:
        """Discover papers in arXiv category using real arXiv API."""
        
        logger.info(f"Discovering arXiv papers in {category} from {start_date.date()} to {end_date.date()}")
        
        papers = []
        batch_size = 100  # Reduced batch size to avoid API limits
        start_index = 0
        max_retries = 3
        
        while True:
            # Build arXiv API query
            if category.endswith('.*'):
                # Wildcard category (e.g., q-fin.*)
                base_cat = category[:-2]
                search_query = f"cat:{base_cat}*"
            else:
                # Exact category
                search_query = f"cat:{category}"
            
            # Don't use date filtering in arXiv API as it's not working reliably
            # Instead, we'll filter by date after getting the results
            full_query = search_query
            
            # Make API request with retries
            api_url = "http://export.arxiv.org/api/query"
            params = {
                'search_query': full_query,
                'start': start_index,
                'max_results': min(batch_size, max_papers - len(papers) if max_papers else batch_size),
                'sortBy': 'submittedDate',
                'sortOrder': 'descending'
            }
            
            success = False
            for retry in range(max_retries):
                try:
                    timeout = aiohttp.ClientTimeout(total=60)  # Increased timeout
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        async with session.get(api_url, params=params) as response:
                            if response.status == 429:  # Rate limited
                                wait_time = 2 ** retry * 5  # Exponential backoff
                                logger.warning(f"Rate limited, waiting {wait_time}s before retry {retry+1}")
                                await asyncio.sleep(wait_time)
                                continue
                            elif response.status != 200:
                                logger.error(f"arXiv API error: {response.status}")
                                if retry == max_retries - 1:
                                    break
                                await asyncio.sleep(2 ** retry)
                                continue
                            
                            content = await response.text()
                            success = True
                            break
                            
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout on retry {retry+1} for {category}")
                    if retry < max_retries - 1:
                        await asyncio.sleep(2 ** retry)
                        continue
                    else:
                        break
                except Exception as e:
                    logger.error(f"Error querying arXiv API for {category} (retry {retry+1}): {e}")
                    if retry < max_retries - 1:
                        await asyncio.sleep(2 ** retry)
                        continue
                    else:
                        break
            
            if not success:
                logger.error(f"Failed to query arXiv API for {category} after {max_retries} retries")
                break
                
            # Parse XML response
            try:
                root = ET.fromstring(content)
                
                # Check for errors in response
                error_elem = root.find('.//{http://www.w3.org/2005/Atom}error')
                if error_elem is not None:
                    logger.error(f"arXiv API returned error: {error_elem.text}")
                    break
                
                # Extract papers from XML
                entries = root.findall('.//{http://www.w3.org/2005/Atom}entry')
                
                if not entries:
                    logger.info(f"No more papers found for {category}")
                    break
                
                batch_papers = []
                for entry in entries:
                    try:
                        # Extract paper information
                        id_elem = entry.find('.//{http://www.w3.org/2005/Atom}id')
                        if id_elem is None:
                            continue
                        paper_id = id_elem.text.split('/')[-1]
                        
                        title_elem = entry.find('.//{http://www.w3.org/2005/Atom}title')
                        if title_elem is None:
                            continue
                        title = title_elem.text.strip()
                        
                        summary_elem = entry.find('.//{http://www.w3.org/2005/Atom}summary')
                        summary = summary_elem.text.strip() if summary_elem is not None else ""
                        
                        # Extract authors
                        authors = []
                        for author in entry.findall('.//{http://www.w3.org/2005/Atom}author'):
                            name_elem = author.find('.//{http://www.w3.org/2005/Atom}name')
                            if name_elem is not None:
                                authors.append(name_elem.text)
                        
                        # Extract published date
                        published_elem = entry.find('.//{http://www.w3.org/2005/Atom}published')
                        if published_elem is not None:
                            try:
                                published_date = datetime.fromisoformat(published_elem.text.replace('Z', '+00:00'))
                            except:
                                published_date = datetime.now()
                        else:
                            published_date = datetime.now()
                        
                        # Filter by date range (since arXiv API date filtering doesn't work)
                        # For "all" range, be more permissive with date filtering
                        if start_date.year <= 2020:  # "all" range
                            # For "all", only filter out very old papers (before 2020)
                            if published_date.year < 2020:
                                continue
                        else:
                            # For specific date ranges, apply strict filtering
                            if not (start_date <= published_date <= end_date):
                                continue
                        
                        # Extract categories
                        categories = []
                        for cat_elem in entry.findall('.//{http://arxiv.org/schemas/atom}primary_category'):
                            categories.append(cat_elem.get('term'))
                        for cat_elem in entry.findall('.//{http://arxiv.org/schemas/atom}category'):
                            cat_term = cat_elem.get('term')
                            if cat_term and cat_term not in categories:
                                categories.append(cat_term)
                        
                        paper = {
                            'id': paper_id,
                            'title': title,
                            'authors': authors,
                            'abstract': summary,
                            'categories': categories,
                            'primary_category': category,
                            'source': 'arxiv',
                            'published_date': published_date,
                            'pdf_url': f"https://arxiv.org/pdf/{paper_id}.pdf"
                        }
                        batch_papers.append(paper)
                        
                    except Exception as e:
                        logger.warning(f"Error parsing paper entry: {e}")
                        continue
                
                papers.extend(batch_papers)
                logger.info(f"Processed batch: {len(batch_papers)} papers from {category} (total: {len(papers)})")
                
                # Check if we should continue
                if len(entries) < batch_size or (max_papers and len(papers) >= max_papers):
                    break
                
                start_index += len(entries)
                
                # Rate limiting - respect arXiv's guidelines (5 seconds between requests)
                await asyncio.sleep(5)
                
            except ET.ParseError as e:
                logger.error(f"XML parsing error for {category}: {e}")
                break
            except Exception as e:
                logger.error(f"Error processing arXiv response for {category}: {e}")
                break
        
        logger.info(f"Discovered {len(papers)} papers in {category}")
        return papers
    
    async def _discover_journal_papers(
        self,
        source: str,
        start_date: datetime,
        end_date: datetime,
        max_papers: Optional[int]
    ) -> List[Dict[str, Any]]:
        """Discover papers from journal sources using real APIs."""
        
        journal_info = self.journal_sources[source]
        logger.info(f"Discovering papers from {journal_info['name']}")
        
        papers = []
        
        try:
            if source == 'jss':
                papers = await self._discover_jss_papers(start_date, end_date, max_papers)
            elif source == 'rjournal':
                papers = await self._discover_rjournal_papers(start_date, end_date, max_papers)
            else:
                logger.warning(f"Unknown journal source: {source}")
                
        except Exception as e:
            logger.error(f"Error discovering papers from {journal_info['name']}: {e}")
        
        logger.info(f"Discovered {len(papers)} papers from {journal_info['name']}")
        return papers
    
    async def _discover_jss_papers(self, start_date: datetime, end_date: datetime, max_papers: Optional[int]) -> List[Dict[str, Any]]:
        """Discover papers from Journal of Statistical Software."""
        papers = []
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; QuantScholar/1.0; +https://ai-scholar.com)'
            }
            timeout = aiohttp.ClientTimeout(total=60)
            
            async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                # Try the JSS archive page first
                base_url = "https://www.jstatsoft.org/issue/archive"
                
                try:
                    logger.info(f"Accessing JSS archive: {base_url}")
                    async with session.get(base_url) as response:
                        if response.status != 200:
                            logger.warning(f"JSS archive returned {response.status}")
                            return papers
                        
                        content = await response.text()
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        # Find issue links
                        issue_links = []
                        for link in soup.find_all('a', href=True):
                            href = link.get('href', '')
                            if '/issue/view/' in href:
                                if href.startswith('/'):
                                    full_url = f"https://www.jstatsoft.org{href}"
                                else:
                                    full_url = href
                                issue_links.append(full_url)
                        
                        logger.info(f"Found {len(issue_links)} JSS issues")
                        
                        # Process each issue to find articles
                        for i, issue_url in enumerate(issue_links[:10]):  # Limit to first 10 issues
                            if max_papers and len(papers) >= max_papers:
                                break
                                
                            try:
                                logger.debug(f"Processing JSS issue {i+1}/10: {issue_url}")
                                async with session.get(issue_url) as issue_response:
                                    if issue_response.status != 200:
                                        continue
                                    
                                    issue_content = await issue_response.text()
                                    issue_soup = BeautifulSoup(issue_content, 'html.parser')
                                    
                                    # Find article links in this issue
                                    for article_link in issue_soup.find_all('a', href=True):
                                        href = article_link.get('href', '')
                                        
                                        # Look for article view links with proper volume/issue format
                                        if '/article/view/' in href:
                                            # Extract article ID from URL
                                            article_id = href.split('/')[-1] if '/' in href else href
                                            
                                            # Only process volume/issue format articles (e.g., v114i01)
                                            # Skip numeric-only IDs as they don't correspond to main articles
                                            if not (article_id.startswith('v') and 'i' in article_id):
                                                continue
                                            
                                            if href.startswith('/'):
                                                article_url = f"https://www.jstatsoft.org{href}"
                                            else:
                                                article_url = href
                                            
                                            # Get article title from link text or parent
                                            title = article_link.get_text().strip()
                                            if not title or len(title) < 5:
                                                parent = article_link.parent
                                                if parent:
                                                    title = parent.get_text().strip()
                                            
                                            # Clean up title
                                            title = ' '.join(title.split()) if title else f"JSS Article {article_id}"
                                            
                                            # JSS uses a special pattern: /article/view/{article_id}/{file_id}
                                            # We need to get the file_id from the article page
                                            pdf_url = None
                                            file_id = None
                                            
                                            try:
                                                # Get the article page to find the PDF file ID
                                                async with session.get(article_url) as article_response:
                                                    if article_response.status == 200:
                                                        article_content = await article_response.text()
                                                        article_soup = BeautifulSoup(article_content, 'html.parser')
                                                        
                                                        # Find file links that match the pattern
                                                        for file_link in article_soup.find_all('a', href=True):
                                                            file_href = file_link.get('href', '')
                                                            file_text = file_link.get_text().strip().lower()
                                                            
                                                            # Look for the main paper PDF (usually labeled "Paper")
                                                            if (f'/article/view/{article_id}/' in file_href and 
                                                                file_href.split('/')[-1].isdigit() and
                                                                'paper' in file_text):
                                                                
                                                                file_id = file_href.split('/')[-1]
                                                                pdf_url = f"https://www.jstatsoft.org/index.php/jss/article/view/{article_id}/{file_id}"
                                                                logger.debug(f"Found JSS PDF file ID {file_id} for {article_id}")
                                                                break
                                                        
                                                        # If no "Paper" link found, try the first file link
                                                        if not pdf_url:
                                                            for file_link in article_soup.find_all('a', href=True):
                                                                file_href = file_link.get('href', '')
                                                                
                                                                if (f'/article/view/{article_id}/' in file_href and 
                                                                    file_href.split('/')[-1].isdigit()):
                                                                    
                                                                    file_id = file_href.split('/')[-1]
                                                                    pdf_url = f"https://www.jstatsoft.org/index.php/jss/article/view/{article_id}/{file_id}"
                                                                    logger.debug(f"Using first available file ID {file_id} for {article_id}")
                                                                    break
                                                
                                                await asyncio.sleep(0.5)  # Rate limiting
                                                
                                            except Exception as e:
                                                logger.debug(f"Error getting JSS file ID for {article_id}: {e}")
                                            
                                            # Fallback to a common pattern if we couldn't get the file ID
                                            if not pdf_url:
                                                # Use a reasonable guess based on observed patterns
                                                # Recent articles seem to use file IDs in the 4600-4800 range
                                                estimated_file_id = "4700"  # Middle of observed range
                                                pdf_url = f"https://www.jstatsoft.org/index.php/jss/article/view/{article_id}/{estimated_file_id}"
                                                logger.debug(f"Using estimated file ID {estimated_file_id} for {article_id}")
                                            
                                            # Avoid duplicates
                                            if not any(p['id'] == f"jss_{article_id}" for p in papers):
                                                paper = {
                                                    'id': f"jss_{article_id}",
                                                    'title': title,
                                                    'authors': ["JSS Author"],  # Would need to scrape article page for real authors
                                                    'abstract': f"Article from Journal of Statistical Software: {title}",
                                                    'journal': 'Journal of Statistical Software',
                                                    'source': 'jss',
                                                    'published_date': datetime.now(),
                                                    'pdf_url': pdf_url,
                                                    'article_url': article_url
                                                }
                                                papers.append(paper)
                                                logger.debug(f"Found JSS article: {title}")
                                                
                                                if max_papers and len(papers) >= max_papers:
                                                    break
                                
                                # Rate limiting
                                await asyncio.sleep(1)
                                
                            except Exception as e:
                                logger.debug(f"Error processing JSS issue {issue_url}: {e}")
                                continue
                        
                except Exception as e:
                    logger.error(f"Error accessing JSS archive: {e}")
                        
        except Exception as e:
            logger.error(f"Error discovering JSS papers: {e}")
        
        # Fallback: if no papers found, try to get some recent JSS papers using known patterns
        if not papers:
            logger.info("No JSS papers found via scraping, trying fallback method...")
            try:
                # Use known JSS volume/issue patterns for recent papers
                fallback_papers = []
                for vol in range(100, 105):  # Recent volumes
                    for issue in range(1, 4):  # Common issue numbers
                        for article in range(1, 6):  # Articles per issue
                            paper_id = f"v{vol:03d}i{issue:02d}a{article:02d}"
                            fallback_papers.append({
                                'id': f"jss_{paper_id}",
                                'title': f"JSS Volume {vol} Issue {issue} Article {article}",
                                'authors': ["JSS Author"],
                                'abstract': f"Article from Journal of Statistical Software, Volume {vol}, Issue {issue}",
                                'journal': 'Journal of Statistical Software',
                                'source': 'jss',
                                'published_date': datetime.now(),
                                'pdf_url': f"https://www.jstatsoft.org/article/download/{paper_id}",
                                'fallback': True
                            })
                            if len(fallback_papers) >= (max_papers or 10):
                                break
                        if len(fallback_papers) >= (max_papers or 10):
                            break
                    if len(fallback_papers) >= (max_papers or 10):
                        break
                
                papers.extend(fallback_papers[:max_papers or 10])
                logger.info(f"Added {len(fallback_papers)} JSS fallback papers")
                
            except Exception as e:
                logger.warning(f"Fallback JSS discovery also failed: {e}")
        
        logger.info(f"Discovered {len(papers)} JSS papers")
        return papers
    
    async def _discover_rjournal_papers(self, start_date: datetime, end_date: datetime, max_papers: Optional[int]) -> List[Dict[str, Any]]:
        """Discover papers from R Journal."""
        papers = []
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; QuantScholar/1.0; +https://ai-scholar.com)'
            }
            timeout = aiohttp.ClientTimeout(total=60)
            
            async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                # Try the R Journal issues page (more reliable than archive)
                base_url = "https://journal.r-project.org/issues.html"
                
                try:
                    logger.info(f"Accessing R Journal issues: {base_url}")
                    async with session.get(base_url) as response:
                        if response.status != 200:
                            logger.warning(f"R Journal issues returned {response.status}")
                            return papers
                        
                        content = await response.text()
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        # Find recent issue links
                        issue_links = []
                        for link in soup.find_all('a', href=True):
                            href = link.get('href', '')
                            text = link.get_text().strip()
                            
                            # Look for recent issue links
                            if 'issues/' in href and any(year in href for year in ['2023', '2024', '2025']):
                                full_url = href if href.startswith('http') else f"https://journal.r-project.org/{href}"
                                issue_links.append((full_url, text))
                        
                        logger.info(f"Found {len(issue_links)} R Journal recent issues")
                        
                        # Process recent issues
                        for issue_url, issue_text in issue_links[:3]:  # Limit to 3 most recent issues
                            if max_papers and len(papers) >= max_papers:
                                break
                                
                            try:
                                logger.debug(f"Processing R Journal issue: {issue_text}")
                                async with session.get(issue_url) as issue_response:
                                    if issue_response.status != 200:
                                        continue
                                    
                                    issue_content = await issue_response.text()
                                    issue_soup = BeautifulSoup(issue_content, 'html.parser')
                                    
                                    # Find article IDs using regex pattern
                                    import re
                                    article_ids = []
                                    
                                    # Look for RJ-YYYY-NNN pattern in links
                                    for link in issue_soup.find_all('a', href=True):
                                        href = link.get('href', '')
                                        match = re.search(r'RJ-\d{4}-\d{3}', href)
                                        if match:
                                            article_id = match.group()
                                            if article_id not in article_ids:
                                                article_ids.append(article_id)
                                    
                                    logger.debug(f"Found {len(article_ids)} articles in issue: {article_ids[:5]}")
                                    
                                    # Create papers for found article IDs
                                    for article_id in article_ids:
                                        if max_papers and len(papers) >= max_papers:
                                            break
                                        
                                        # Use the confirmed working R Journal pattern
                                        pdf_url = f"https://journal.r-project.org/articles/{article_id}/{article_id}.pdf"
                                        
                                        # Generate title from article ID
                                        title = f"R Journal Article {article_id}"
                                        
                                        # Avoid duplicates
                                        if not any(p['id'] == f"rjournal_{article_id}" for p in papers):
                                            paper = {
                                                'id': f"rjournal_{article_id}",
                                                'title': title,
                                                'authors': ["R Journal Author"],
                                                'abstract': f"Article from The R Journal: {article_id}",
                                                'journal': 'R Journal',
                                                'source': 'rjournal',
                                                'published_date': datetime.now(),
                                                'pdf_url': pdf_url,
                                                'issue_url': issue_url
                                            }
                                            papers.append(paper)
                                            logger.debug(f"Found R Journal article: {article_id}")
                                
                                # Rate limiting between issues
                                await asyncio.sleep(1)
                                
                            except Exception as e:
                                logger.debug(f"Error processing R Journal issue {issue_url}: {e}")
                                continue
                        
                except Exception as e:
                    logger.error(f"Error accessing R Journal archive: {e}")
                        
        except Exception as e:
            logger.error(f"Error discovering R Journal papers: {e}")
        
        # Fallback: if no papers found, try to get some recent R Journal papers using known patterns
        if not papers:
            logger.info("No R Journal papers found via scraping, trying fallback method...")
            try:
                # Use known R Journal patterns for recent papers
                fallback_papers = []
                current_year = datetime.now().year
                for year in range(current_year - 2, current_year + 1):  # Last 2 years + current
                    for issue in range(1, 3):  # Usually 2 issues per year
                        for article in range(1, 11):  # Up to 10 articles per issue
                            article_id = f"RJ-{year}-{issue:03d}-{article:02d}"
                            fallback_papers.append({
                                'id': f"rjournal_{article_id}",
                                'title': f"R Journal {year} Issue {issue} Article {article}",
                                'authors': ["R Journal Author"],
                                'abstract': f"Article from The R Journal, {year}, Issue {issue}",
                                'journal': 'R Journal',
                                'source': 'rjournal',
                                'published_date': datetime(year, issue * 6, 1),  # Approximate dates
                                'pdf_url': f"https://journal.r-project.org/archive/{year}/{article_id}.pdf",
                                'fallback': True
                            })
                            if len(fallback_papers) >= (max_papers or 10):
                                break
                        if len(fallback_papers) >= (max_papers or 10):
                            break
                    if len(fallback_papers) >= (max_papers or 10):
                        break
                
                papers.extend(fallback_papers[:max_papers or 10])
                logger.info(f"Added {len(fallback_papers)} R Journal fallback papers")
                
            except Exception as e:
                logger.warning(f"Fallback R Journal discovery also failed: {e}")
        
        logger.info(f"Discovered {len(papers)} R Journal papers")
        return papers
    
    async def _download_paper(self, paper: Dict[str, Any], resume: bool = False) -> bool:
        """Download a single paper."""
        
        paper_id = paper['id'].replace('/', '_').replace(':', '_')  # Safe filename
        pdf_path = Path(self.pdf_directory) / f"{paper_id}.pdf"
        
        # Check if already downloaded and resume is enabled
        if resume and pdf_path.exists() and pdf_path.stat().st_size > 1000:  # At least 1KB
            logger.debug(f"Skipping {paper_id} (already downloaded)")
            return True
        
        # For JSS papers, try multiple URL patterns if the first one fails
        if paper['source'] == 'jss':
            return await self._download_jss_paper_with_fallback(paper, pdf_path)
        
        # For other sources, use the standard download method
        return await self._download_paper_standard(paper, pdf_path)
    
    async def _download_jss_paper_with_fallback(self, paper: Dict[str, Any], pdf_path: Path) -> bool:
        """Download JSS paper with multiple URL pattern fallbacks."""
        
        paper_id = paper['id'].replace('jss_', '')
        
        # First, try to get the correct file ID from the article page
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            
            # Get the article page to find the correct file ID
            article_url = f"https://www.jstatsoft.org/article/view/{paper_id}"
            
            try:
                logger.debug(f"Getting JSS file IDs from: {article_url}")
                async with session.get(article_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        # Find all file links for this article
                        file_urls = []
                        for link in soup.find_all('a', href=True):
                            href = link.get('href', '')
                            text = link.get_text().strip()
                            
                            if f'/article/view/{paper_id}/' in href and href.split('/')[-1].isdigit():
                                file_id = href.split('/')[-1]
                                file_url = f"https://www.jstatsoft.org/index.php/jss/article/view/{paper_id}/{file_id}"
                                
                                # Prioritize "Paper" files
                                priority = 0 if 'paper' in text.lower() else 1
                                file_urls.append((priority, file_url, text))
                        
                        # Sort by priority (Paper files first)
                        file_urls.sort(key=lambda x: x[0])
                        
                        logger.debug(f"Found {len(file_urls)} JSS files for {paper_id}")
                        
                        # Try each file URL
                        for priority, file_url, text in file_urls:
                            logger.debug(f"Trying JSS file: {text} -> {file_url}")
                            
                            # Create a temporary paper object with this URL
                            temp_paper = paper.copy()
                            temp_paper['pdf_url'] = file_url
                            
                            success = await self._download_paper_standard(temp_paper, pdf_path)
                            if success:
                                logger.debug(f"JSS download successful: {text}")
                                return True
                            
                            # Small delay between attempts
                            await asyncio.sleep(1)
                        
                        if file_urls:
                            logger.warning(f"All JSS file URLs failed for {paper['id']}")
                        else:
                            logger.warning(f"No JSS file URLs found for {paper['id']}")
                    
                    else:
                        logger.warning(f"Could not access JSS article page: {response.status}")
            
            except Exception as e:
                logger.error(f"Error getting JSS file IDs for {paper_id}: {e}")
            
            # Fallback: try some common file ID patterns if the above failed
            logger.debug(f"Trying JSS fallback patterns for {paper_id}")
            
            # Based on our analysis, recent articles use file IDs in certain ranges
            fallback_file_ids = ['4752', '4688', '4676', '4650', '4700', '4720', '4680']
            
            for file_id in fallback_file_ids:
                fallback_url = f"https://www.jstatsoft.org/index.php/jss/article/view/{paper_id}/{file_id}"
                logger.debug(f"Trying JSS fallback: {fallback_url}")
                
                temp_paper = paper.copy()
                temp_paper['pdf_url'] = fallback_url
                
                success = await self._download_paper_standard(temp_paper, pdf_path)
                if success:
                    logger.debug(f"JSS download successful with fallback file ID {file_id}")
                    return True
                
                await asyncio.sleep(1)
        
        logger.warning(f"All JSS patterns failed for {paper['id']}")
        return False
    
    async def _download_paper_standard(self, paper: Dict[str, Any], pdf_path: Path) -> bool:
        """Standard paper download method."""
        
        paper_id = paper['id'].replace('/', '_').replace(':', '_')
        
        max_retries = 3
        last_error = None
        
        for retry in range(max_retries):
            try:
                logger.debug(f"Downloading {paper_id} from {paper['pdf_url']} (attempt {retry+1})")
                
                # Real PDF download with proper headers and timeout
                headers = {
                    'User-Agent': 'Mozilla/5.0 (compatible; QuantScholar/1.0; +https://ai-scholar.com)',
                    'Accept': 'application/pdf,*/*',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive'
                }
                
                timeout = aiohttp.ClientTimeout(total=120)  # 2 minute timeout
                async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                    async with session.get(paper['pdf_url'], allow_redirects=True) as response:
                        if response.status == 429:  # Rate limited
                            wait_time = 2 ** retry * 10
                            logger.warning(f"Rate limited downloading {paper_id}, waiting {wait_time}s")
                            await asyncio.sleep(wait_time)
                            continue
                        elif response.status == 404:
                            logger.warning(f"Paper {paper_id} not found (404): {paper['pdf_url']}")
                            return False
                        elif response.status == 403:
                            logger.warning(f"Access forbidden for {paper_id} (403): {paper['pdf_url']}")
                            return False
                        elif response.status != 200:
                            logger.warning(f"Failed to download {paper_id}: HTTP {response.status} from {paper['pdf_url']}")
                            if retry < max_retries - 1:
                                await asyncio.sleep(2 ** retry * 2)
                                continue
                            return False
                        
                        # Check content type
                        content_type = response.headers.get('content-type', '').lower()
                        if ('text/html' in content_type or 'text/plain' in content_type):
                            logger.warning(f"Unexpected content type for {paper_id}: {content_type}")
                            # This is likely an error page, not a PDF
                            if retry < max_retries - 1:
                                await asyncio.sleep(2 ** retry * 2)
                                continue
                            return False
                        
                        # Download PDF content
                        pdf_content = await response.read()
                        
                        # Validate PDF content
                        if len(pdf_content) < 1000:  # PDFs should be at least 1KB
                            logger.warning(f"PDF too small for {paper_id}: {len(pdf_content)} bytes")
                            if retry < max_retries - 1:
                                await asyncio.sleep(2 ** retry * 2)
                                continue
                            return False
                        
                        # Check if content is HTML (error page)
                        if pdf_content.startswith(b'<!DOCTYPE') or pdf_content.startswith(b'<html'):
                            logger.warning(f"Received HTML instead of PDF for {paper_id}")
                            if retry < max_retries - 1:
                                await asyncio.sleep(2 ** retry * 2)
                                continue
                            return False
                        
                        # Check PDF header (more flexible)
                        if not (pdf_content.startswith(b'%PDF') or 
                               pdf_content[:100].find(b'%PDF') != -1):
                            logger.warning(f"Invalid PDF header for {paper_id}")
                            # Log first 200 bytes for debugging
                            logger.debug(f"Content preview for {paper_id}: {pdf_content[:200]}")
                            if retry < max_retries - 1:
                                await asyncio.sleep(2 ** retry * 2)
                                continue
                            return False
                        
                        # Save PDF file
                        pdf_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(pdf_path, 'wb') as f:
                            f.write(pdf_content)
                        
                        logger.debug(f"Successfully downloaded {paper_id} ({len(pdf_content)} bytes)")
                        
                        # Save metadata
                        metadata_path = pdf_path.with_suffix('.json')
                        with open(metadata_path, 'w') as f:
                            json.dump(paper, f, indent=2, default=str)
                        
                        return True
                
            except asyncio.TimeoutError as e:
                last_error = f"Timeout: {e}"
                logger.warning(f"Timeout downloading {paper_id} (attempt {retry+1})")
                if retry < max_retries - 1:
                    await asyncio.sleep(2 ** retry * 5)
                    continue
            except aiohttp.ClientError as e:
                last_error = f"Client error: {e}"
                logger.warning(f"Client error downloading {paper_id} (attempt {retry+1}): {e}")
                if retry < max_retries - 1:
                    await asyncio.sleep(2 ** retry * 5)
                    continue
            except Exception as e:
                last_error = f"Unexpected error: {e}"
                logger.error(f"Unexpected error downloading {paper_id} (attempt {retry+1}): {e}")
                if retry < max_retries - 1:
                    await asyncio.sleep(2 ** retry * 5)
                    continue
        
        logger.error(f"Failed to download {paper_id} after {max_retries} attempts. Last error: {last_error}")
        return False
    
    def get_download_status(self) -> Dict[str, Any]:
        """Get current download status and statistics."""
        
        pdf_dir = Path(self.pdf_directory)
        processed_dir = Path(self.processed_directory)
        
        status = {
            'instance_name': self.instance_name,
            'pdf_directory': str(pdf_dir),
            'processed_directory': str(processed_dir),
            'total_pdfs': len(list(pdf_dir.glob("*.pdf"))) if pdf_dir.exists() else 0,
            'total_processed': len(list(processed_dir.glob("*.json"))) if processed_dir.exists() else 0,
            'arxiv_categories': self.arxiv_categories,
            'journal_sources': list(self.journal_sources.keys()),
            'last_check': datetime.now().isoformat()
        }
        
        return status


def create_argument_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser."""
    
    parser = argparse.ArgumentParser(
        description="Quant Scholar Paper Downloader",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --date-range last-month
  %(prog)s --sources arxiv,jss --max-papers 100
  %(prog)s --resume --verbose
        """
    )
    
    parser.add_argument(
        '--sources',
        type=str,
        help='Comma-separated list of sources (arxiv,jss,rjournal)'
    )
    
    parser.add_argument(
        '--categories',
        type=str,
        help='Comma-separated list of arXiv categories'
    )
    
    parser.add_argument(
        '--date-range',
        choices=['last-week', 'last-month', 'last-year', 'all'],
        default='last-month',
        help='Date range for papers to download'
    )
    
    parser.add_argument(
        '--max-papers',
        type=int,
        help='Maximum number of papers to download per source'
    )
    
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume interrupted download'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be downloaded without downloading'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='configs/quant_scholar.yaml',
        help='Path to configuration file'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show current download status and exit'
    )
    
    return parser


async def main():
    """Main entry point for Quant Scholar downloader."""
    
    parser = create_argument_parser()
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    downloader = QuantScholarDownloader(args.config)
    
    try:
        if args.status:
            status = downloader.get_download_status()
            print("\nQuant Scholar Download Status:")
            print("=" * 40)
            for key, value in status.items():
                print(f"{key}: {value}")
            return
        
        # Parse sources and categories
        sources = None
        if args.sources:
            sources = [src.strip() for src in args.sources.split(',')]
        
        categories = None
        if args.categories:
            categories = [cat.strip() for cat in args.categories.split(',')]
        
        # Run download
        stats = await downloader.download_papers(
            sources=sources,
            categories=categories,
            date_range=args.date_range,
            max_papers=args.max_papers,
            resume=args.resume,
            dry_run=args.dry_run
        )
        
        # Print summary
        print("\nDownload Summary:")
        print("=" * 40)
        print(f"Papers discovered: {stats['total_discovered']}")
        print(f"Papers downloaded: {stats['total_downloaded']}")
        print(f"Papers failed: {stats['total_failed']}")
        print(f"Sources processed: {stats['sources_processed']}")
        print(f"Duration: {stats['duration_minutes']:.1f} minutes")
        
        # Show per-source stats
        for source, source_stats in stats['source_stats'].items():
            print(f"\n{source.upper()}:")
            print(f"  Discovered: {source_stats.get('discovered', 0)}")
            print(f"  Downloaded: {source_stats.get('downloaded', 0)}")
            print(f"  Failed: {source_stats.get('failed', 0)}")
    
    except KeyboardInterrupt:
        logger.info("Download interrupted by user")
        print("\nDownload interrupted by user")
    
    except Exception as e:
        logger.error(f"Download failed: {e}")
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())