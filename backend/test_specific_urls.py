#!/usr/bin/env python3
"""
Test specific URLs to understand the actual structure
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup

async def test_specific_jss_url():
    """Test a specific JSS URL to understand the structure."""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        
        # Test a known JSS article page
        article_url = "https://www.jstatsoft.org/article/view/v114i01"
        
        print(f"Testing JSS article page: {article_url}")
        
        try:
            async with session.get(article_url) as response:
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    print("Looking for download links...")
                    
                    # Find all links
                    for link in soup.find_all('a', href=True):
                        href = link.get('href', '')
                        text = link.get_text().strip()
                        
                        # Look for PDF or download related links
                        if any(keyword in href.lower() for keyword in ['pdf', 'download', 'galley']):
                            full_url = href if href.startswith('http') else f"https://www.jstatsoft.org{href}"
                            print(f"  Found: {text[:50]} -> {full_url}")
                            
                            # Test this URL
                            try:
                                async with session.head(full_url) as test_response:
                                    print(f"    Status: {test_response.status}")
                                    print(f"    Content-Type: {test_response.headers.get('content-type', 'unknown')}")
                                    print(f"    Content-Length: {test_response.headers.get('content-length', 'unknown')}")
                            except Exception as e:
                                print(f"    Error testing URL: {e}")
                            
                            await asyncio.sleep(0.5)
                else:
                    print(f"Failed to access article page: {response.status}")
                    
        except Exception as e:
            print(f"Error: {e}")

async def test_specific_rjournal_url():
    """Test a specific R Journal URL to understand the structure."""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        
        # Test the R Journal archive that returned 200
        test_url = "https://journal.r-project.org/archive/RJ-2021-048.pdf"
        
        print(f"\nTesting R Journal URL: {test_url}")
        
        try:
            async with session.get(test_url) as response:
                print(f"Status: {response.status}")
                print(f"Content-Type: {response.headers.get('content-type', 'unknown')}")
                print(f"Content-Length: {response.headers.get('content-length', 'unknown')}")
                
                if response.status == 200:
                    content = await response.text()
                    
                    # Check if it's HTML (article page) or PDF
                    if content.startswith('<!DOCTYPE') or '<html' in content[:100]:
                        print("This is an HTML page, not a PDF")
                        
                        # Parse the HTML to find the actual PDF link
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        print("Looking for PDF download links...")
                        for link in soup.find_all('a', href=True):
                            href = link.get('href', '')
                            text = link.get_text().strip()
                            
                            if 'pdf' in href.lower() or 'download' in text.lower():
                                full_url = href if href.startswith('http') else f"https://journal.r-project.org{href}"
                                print(f"  Found: {text[:50]} -> {full_url}")
                    else:
                        print("This appears to be binary content (possibly PDF)")
                        print(f"First 100 bytes: {content[:100]}")
                        
        except Exception as e:
            print(f"Error: {e}")

async def test_rjournal_archive_structure():
    """Test R Journal archive structure."""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        
        # Test the main archive page
        archive_url = "https://journal.r-project.org/archive/"
        
        print(f"\nTesting R Journal archive: {archive_url}")
        
        try:
            async with session.get(archive_url) as response:
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    print("Archive page structure:")
                    
                    # Look for any links
                    links = soup.find_all('a', href=True)
                    print(f"Found {len(links)} total links")
                    
                    # Categorize links
                    year_links = []
                    pdf_links = []
                    other_links = []
                    
                    for link in links:
                        href = link.get('href', '')
                        text = link.get_text().strip()
                        
                        if href.endswith('/') and len(href) <= 6 and any(c.isdigit() for c in href):
                            year_links.append((href, text))
                        elif href.endswith('.pdf'):
                            pdf_links.append((href, text))
                        elif text and len(text) > 3:
                            other_links.append((href, text))
                    
                    print(f"\nYear-like directories: {len(year_links)}")
                    for href, text in year_links[:10]:
                        print(f"  {text} -> {href}")
                    
                    print(f"\nDirect PDF links: {len(pdf_links)}")
                    for href, text in pdf_links[:10]:
                        print(f"  {text} -> {href}")
                    
                    print(f"\nOther interesting links: {len(other_links)}")
                    for href, text in other_links[:10]:
                        if len(text) < 100:  # Skip very long text
                            print(f"  {text} -> {href}")
                        
        except Exception as e:
            print(f"Error: {e}")

async def main():
    """Main test function."""
    print("Specific URL Structure Test")
    print("=" * 50)
    
    await test_specific_jss_url()
    await test_specific_rjournal_url()
    await test_rjournal_archive_structure()

if __name__ == "__main__":
    asyncio.run(main())