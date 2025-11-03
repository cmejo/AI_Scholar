#!/usr/bin/env python3
"""
URL Validation Test Script for Journal Downloads

This script tests different URL patterns for JSS and R Journal to find working ones.
"""

import asyncio
import aiohttp
from pathlib import Path
import sys

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

async def test_url(session, url, description=""):
    """Test if a URL returns a valid response."""
    try:
        async with session.head(url, allow_redirects=True) as response:
            status = response.status
            content_type = response.headers.get('content-type', '')
            content_length = response.headers.get('content-length', 'unknown')
            
            result = {
                'url': url,
                'status': status,
                'content_type': content_type,
                'content_length': content_length,
                'valid': status == 200,
                'is_pdf': 'pdf' in content_type.lower() or 'application/octet-stream' in content_type.lower()
            }
            
            print(f"{'✓' if result['valid'] else '✗'} {description}")
            print(f"  URL: {url}")
            print(f"  Status: {status}")
            print(f"  Content-Type: {content_type}")
            print(f"  Content-Length: {content_length}")
            print(f"  Is PDF: {result['is_pdf']}")
            print()
            
            return result
            
    except Exception as e:
        print(f"✗ {description}")
        print(f"  URL: {url}")
        print(f"  Error: {e}")
        print()
        return {'url': url, 'valid': False, 'error': str(e)}

async def test_jss_patterns():
    """Test different JSS URL patterns."""
    print("Testing JSS URL Patterns")
    print("=" * 50)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        
        # Test known JSS article IDs (these should exist)
        test_articles = [
            'v01i01',  # Very first JSS article
            'v100i01', # Recent volume
            'v110i01', # Another recent one
        ]
        
        patterns = [
            "https://www.jstatsoft.org/article/download/{article_id}",
            "https://www.jstatsoft.org/article/download/{article_id}/0", 
            "https://www.jstatsoft.org/index.php/jss/article/download/{article_id}",
            "https://www.jstatsoft.org/index.php/jss/article/download/{article_id}/0",
            "https://www.jstatsoft.org/article/view/{article_id}/download",
            "https://www.jstatsoft.org/index.php/jss/article/view/{article_id}/download"
        ]
        
        results = []
        for article_id in test_articles:
            print(f"\nTesting article: {article_id}")
            print("-" * 30)
            
            for i, pattern in enumerate(patterns):
                url = pattern.format(article_id=article_id)
                result = await test_url(session, url, f"Pattern {i+1}: {pattern.split('/')[-2:]}")
                results.append(result)
                
                # Rate limiting
                await asyncio.sleep(1)
        
        return results

async def test_rjournal_patterns():
    """Test different R Journal URL patterns."""
    print("\nTesting R Journal URL Patterns")
    print("=" * 50)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        
        # Test known R Journal patterns (these might exist)
        test_articles = [
            ('2021', 'RJ-2021-048'),  # Known format
            ('2022', 'RJ-2022-001'),
            ('2023', 'RJ-2023-001'),
        ]
        
        patterns = [
            "https://journal.r-project.org/archive/{year}/{article_id}.pdf",
            "https://journal.r-project.org/archive/{year}/RJ-{year}-{issue}.pdf",
            "https://journal.r-project.org/articles/{article_id}.pdf",
            "https://journal.r-project.org/archive/{article_id}.pdf"
        ]
        
        results = []
        for year, article_id in test_articles:
            print(f"\nTesting article: {article_id} ({year})")
            print("-" * 30)
            
            for i, pattern in enumerate(patterns):
                if '{issue}' in pattern:
                    # Extract issue number from article_id
                    issue = article_id.split('-')[-1] if '-' in article_id else '001'
                    url = pattern.format(year=year, article_id=article_id, issue=issue)
                else:
                    url = pattern.format(year=year, article_id=article_id)
                
                result = await test_url(session, url, f"Pattern {i+1}")
                results.append(result)
                
                # Rate limiting
                await asyncio.sleep(1)
        
        return results

async def discover_real_jss_urls():
    """Try to discover real JSS URLs by scraping."""
    print("\nDiscovering Real JSS URLs")
    print("=" * 50)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        
        # Get a recent JSS issue page
        issue_url = "https://www.jstatsoft.org/index.php/jss/issue/view/v114"
        
        try:
            async with session.get(issue_url) as response:
                if response.status == 200:
                    from bs4 import BeautifulSoup
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    print(f"Scraping JSS issue: {issue_url}")
                    
                    # Find all links
                    pdf_links = []
                    download_links = []
                    
                    for link in soup.find_all('a', href=True):
                        href = link.get('href', '')
                        text = link.get_text().strip()
                        
                        if 'pdf' in href.lower() or href.endswith('.pdf'):
                            pdf_links.append((href, text))
                        elif 'download' in href.lower():
                            download_links.append((href, text))
                    
                    print(f"\nFound {len(pdf_links)} PDF links:")
                    for href, text in pdf_links[:5]:  # Show first 5
                        full_url = href if href.startswith('http') else f"https://www.jstatsoft.org{href}"
                        print(f"  {text[:50]}... -> {full_url}")
                    
                    print(f"\nFound {len(download_links)} download links:")
                    for href, text in download_links[:5]:  # Show first 5
                        full_url = href if href.startswith('http') else f"https://www.jstatsoft.org{href}"
                        print(f"  {text[:50]}... -> {full_url}")
                    
                    # Test a few of these URLs
                    print(f"\nTesting discovered URLs:")
                    for href, text in (pdf_links + download_links)[:3]:
                        full_url = href if href.startswith('http') else f"https://www.jstatsoft.org{href}"
                        await test_url(session, full_url, f"Discovered: {text[:30]}...")
                        await asyncio.sleep(1)
                        
        except Exception as e:
            print(f"Error scraping JSS: {e}")

async def discover_real_rjournal_urls():
    """Try to discover real R Journal URLs by scraping."""
    print("\nDiscovering Real R Journal URLs")
    print("=" * 50)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        
        # Try the R Journal archive
        archive_url = "https://journal.r-project.org/archive/"
        
        try:
            async with session.get(archive_url) as response:
                if response.status == 200:
                    from bs4 import BeautifulSoup
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    print(f"Scraping R Journal archive: {archive_url}")
                    
                    # Find year directories
                    year_links = []
                    for link in soup.find_all('a', href=True):
                        href = link.get('href', '')
                        if href.endswith('/') and len(href) == 5 and href[:-1].isdigit():
                            year = int(href[:-1])
                            if year >= 2020:  # Recent years
                                year_links.append(f"https://journal.r-project.org/archive/{href}")
                    
                    print(f"Found {len(year_links)} recent year directories")
                    
                    # Check one year directory
                    if year_links:
                        year_url = year_links[0]  # Most recent
                        print(f"\nChecking year directory: {year_url}")
                        
                        async with session.get(year_url) as year_response:
                            if year_response.status == 200:
                                year_content = await year_response.text()
                                year_soup = BeautifulSoup(year_content, 'html.parser')
                                
                                # Find PDF files
                                pdf_files = []
                                for link in year_soup.find_all('a', href=True):
                                    href = link.get('href', '')
                                    if href.endswith('.pdf'):
                                        full_url = f"{year_url.rstrip('/')}/{href}"
                                        pdf_files.append(full_url)
                                
                                print(f"Found {len(pdf_files)} PDF files in year directory")
                                
                                # Test a few PDFs
                                for pdf_url in pdf_files[:3]:
                                    await test_url(session, pdf_url, f"R Journal PDF")
                                    await asyncio.sleep(1)
                        
        except Exception as e:
            print(f"Error scraping R Journal: {e}")

async def main():
    """Main test function."""
    print("Journal URL Validation Test")
    print("=" * 60)
    
    # Test JSS patterns
    jss_results = await test_jss_patterns()
    
    # Test R Journal patterns  
    rjournal_results = await test_rjournal_patterns()
    
    # Discover real URLs
    await discover_real_jss_urls()
    await discover_real_rjournal_urls()
    
    # Summary
    print("\nSummary")
    print("=" * 60)
    
    jss_working = [r for r in jss_results if r.get('valid', False)]
    rjournal_working = [r for r in rjournal_results if r.get('valid', False)]
    
    print(f"JSS: {len(jss_working)}/{len(jss_results)} URLs working")
    print(f"R Journal: {len(rjournal_working)}/{len(rjournal_results)} URLs working")
    
    if jss_working:
        print("\nWorking JSS patterns:")
        for result in jss_working:
            print(f"  ✓ {result['url']}")
    
    if rjournal_working:
        print("\nWorking R Journal patterns:")
        for result in rjournal_working:
            print(f"  ✓ {result['url']}")

if __name__ == "__main__":
    asyncio.run(main())