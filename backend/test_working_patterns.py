#!/usr/bin/env python3
"""
Test to find actual working download patterns for JSS and R Journal
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup

async def find_jss_download_pattern():
    """Find the actual JSS download pattern by examining the page source."""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        
        # Test a known JSS article page
        article_url = "https://www.jstatsoft.org/article/view/v114i01"
        
        print(f"Analyzing JSS article page: {article_url}")
        
        try:
            async with session.get(article_url) as response:
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Look for any mention of PDF in the page
                    print("\nSearching for PDF references in page content...")
                    
                    # Check for PDF in text content
                    if 'pdf' in content.lower():
                        print("Found 'pdf' in page content")
                        
                        # Look for specific patterns
                        import re
                        pdf_patterns = re.findall(r'["\']([^"\']*pdf[^"\']*)["\']', content, re.IGNORECASE)
                        for pattern in pdf_patterns[:10]:
                            print(f"  PDF pattern: {pattern}")
                    
                    # Look for download buttons or links
                    print("\nLooking for download-related elements...")
                    
                    # Check for buttons with download text
                    for button in soup.find_all(['button', 'input'], type=['button', 'submit']):
                        if button.get_text() and 'download' in button.get_text().lower():
                            print(f"  Download button: {button}")
                    
                    # Check for forms that might handle downloads
                    for form in soup.find_all('form'):
                        action = form.get('action', '')
                        if 'download' in action.lower():
                            print(f"  Download form: {action}")
                    
                    # Look for JavaScript that might handle downloads
                    for script in soup.find_all('script'):
                        if script.string and 'download' in script.string.lower():
                            print(f"  Download script found (truncated): {script.string[:200]}...")
                    
                    # Check meta tags for PDF info
                    for meta in soup.find_all('meta'):
                        content_attr = meta.get('content', '')
                        if 'pdf' in content_attr.lower():
                            print(f"  PDF meta: {meta}")
                    
                    # Look for specific JSS patterns
                    print("\nLooking for JSS-specific patterns...")
                    
                    # Check for galley links (common in academic publishing)
                    for link in soup.find_all('a', href=True):
                        href = link.get('href', '')
                        text = link.get_text().strip()
                        
                        if any(keyword in href.lower() for keyword in ['galley', 'view', 'download']):
                            if any(keyword in text.lower() for keyword in ['pdf', 'full', 'text', 'article']):
                                full_url = href if href.startswith('http') else f"https://www.jstatsoft.org{href}"
                                print(f"  Potential download: {text} -> {full_url}")
                                
                                # Test this URL
                                try:
                                    async with session.head(full_url) as test_response:
                                        ct = test_response.headers.get('content-type', '')
                                        if 'pdf' in ct.lower():
                                            print(f"    ✓ This is a PDF! Status: {test_response.status}")
                                        else:
                                            print(f"    Status: {test_response.status}, Content-Type: {ct}")
                                except Exception as e:
                                    print(f"    Error: {e}")
                                
                                await asyncio.sleep(0.5)
                        
        except Exception as e:
            print(f"Error: {e}")

async def find_rjournal_working_urls():
    """Find actual working R Journal URLs."""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        
        print(f"\nAnalyzing R Journal structure...")
        
        # Try the current issues page
        issues_url = "https://journal.r-project.org/issues.html"
        
        try:
            async with session.get(issues_url) as response:
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    print(f"Checking R Journal issues page: {issues_url}")
                    
                    # Look for issue links
                    issue_links = []
                    for link in soup.find_all('a', href=True):
                        href = link.get('href', '')
                        text = link.get_text().strip()
                        
                        if 'issues/' in href or any(year in href for year in ['2021', '2022', '2023', '2024']):
                            full_url = href if href.startswith('http') else f"https://journal.r-project.org/{href}"
                            issue_links.append((full_url, text))
                    
                    print(f"Found {len(issue_links)} issue links")
                    
                    # Check a recent issue
                    if issue_links:
                        issue_url, issue_text = issue_links[0]
                        print(f"\nChecking recent issue: {issue_text} -> {issue_url}")
                        
                        try:
                            async with session.get(issue_url) as issue_response:
                                if issue_response.status == 200:
                                    issue_content = await issue_response.text()
                                    issue_soup = BeautifulSoup(issue_content, 'html.parser')
                                    
                                    # Look for article links in this issue
                                    article_links = []
                                    for link in issue_soup.find_all('a', href=True):
                                        href = link.get('href', '')
                                        text = link.get_text().strip()
                                        
                                        if any(keyword in href.lower() for keyword in ['article', 'rj-']):
                                            full_url = href if href.startswith('http') else f"https://journal.r-project.org/{href}"
                                            article_links.append((full_url, text))
                                    
                                    print(f"Found {len(article_links)} article links in issue")
                                    
                                    # Test a few article links
                                    for article_url, article_text in article_links[:3]:
                                        print(f"\nTesting article: {article_text[:50]}...")
                                        print(f"  URL: {article_url}")
                                        
                                        try:
                                            async with session.get(article_url) as article_response:
                                                if article_response.status == 200:
                                                    article_content = await article_response.text()
                                                    
                                                    # Check if this is a PDF or HTML
                                                    if article_content.startswith('%PDF'):
                                                        print(f"  ✓ This is a PDF! Size: {len(article_content)} bytes")
                                                    else:
                                                        print(f"  This is HTML, looking for PDF links...")
                                                        
                                                        # Parse HTML to find PDF links
                                                        article_soup = BeautifulSoup(article_content, 'html.parser')
                                                        for pdf_link in article_soup.find_all('a', href=True):
                                                            pdf_href = pdf_link.get('href', '')
                                                            pdf_text = pdf_link.get_text().strip()
                                                            
                                                            if 'pdf' in pdf_href.lower() or 'pdf' in pdf_text.lower():
                                                                pdf_full_url = pdf_href if pdf_href.startswith('http') else f"https://journal.r-project.org/{pdf_href}"
                                                                print(f"    Found PDF link: {pdf_text} -> {pdf_full_url}")
                                                                
                                                                # Test the PDF link
                                                                try:
                                                                    async with session.head(pdf_full_url) as pdf_response:
                                                                        ct = pdf_response.headers.get('content-type', '')
                                                                        if 'pdf' in ct.lower():
                                                                            print(f"      ✓ Confirmed PDF! Status: {pdf_response.status}")
                                                                        else:
                                                                            print(f"      Status: {pdf_response.status}, Content-Type: {ct}")
                                                                except Exception as e:
                                                                    print(f"      Error: {e}")
                                                                
                                                                await asyncio.sleep(0.5)
                                                else:
                                                    print(f"  Failed to access article: {article_response.status}")
                                        except Exception as e:
                                            print(f"  Error accessing article: {e}")
                                        
                                        await asyncio.sleep(1)
                                        
                        except Exception as e:
                            print(f"Error accessing issue: {e}")
                        
        except Exception as e:
            print(f"Error: {e}")

async def test_alternative_jss_patterns():
    """Test alternative JSS URL patterns based on common academic publishing systems."""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        
        print(f"\nTesting alternative JSS patterns...")
        
        # Test different JSS URL patterns that might work
        article_id = "v114i01"  # Known article
        
        alternative_patterns = [
            f"https://www.jstatsoft.org/index.php/jss/article/viewFile/{article_id}/0",
            f"https://www.jstatsoft.org/index.php/jss/article/viewFile/{article_id}/1", 
            f"https://www.jstatsoft.org/index.php/jss/article/viewPDFInterstitial/{article_id}/0",
            f"https://www.jstatsoft.org/article/viewFile/{article_id}/0",
            f"https://www.jstatsoft.org/article/viewFile/{article_id}/1",
            f"https://www.jstatsoft.org/index.php/jss/gateway/plugin/WebFeedGatewayPlugin/pdf/{article_id}",
            f"https://www.jstatsoft.org/gateway/plugin/WebFeedGatewayPlugin/pdf/{article_id}",
        ]
        
        for pattern in alternative_patterns:
            print(f"\nTesting: {pattern}")
            
            try:
                async with session.head(pattern) as response:
                    ct = response.headers.get('content-type', '')
                    cl = response.headers.get('content-length', 'unknown')
                    
                    print(f"  Status: {response.status}")
                    print(f"  Content-Type: {ct}")
                    print(f"  Content-Length: {cl}")
                    
                    if response.status == 200 and 'pdf' in ct.lower():
                        print(f"  ✓ SUCCESS! This pattern works for PDFs")
                    elif response.status == 200:
                        print(f"  ⚠ Returns content but not PDF")
                    
            except Exception as e:
                print(f"  Error: {e}")
            
            await asyncio.sleep(1)

async def main():
    """Main test function."""
    print("Working Pattern Discovery Test")
    print("=" * 50)
    
    await find_jss_download_pattern()
    await test_alternative_jss_patterns()
    await find_rjournal_working_urls()

if __name__ == "__main__":
    asyncio.run(main())