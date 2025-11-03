#!/usr/bin/env python3
"""
Comprehensive JSS URL pattern testing to find working download patterns
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re

async def find_working_jss_patterns():
    """Find working JSS download patterns by comprehensive testing."""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    timeout = aiohttp.ClientTimeout(total=60)
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        
        print("=== Comprehensive JSS Pattern Testing ===\n")
        
        # Step 1: Get real article page and analyze its structure
        article_url = "https://www.jstatsoft.org/article/view/v114i01"
        
        print(f"1. Analyzing JSS article page: {article_url}")
        
        try:
            async with session.get(article_url) as response:
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    print("   Looking for download mechanisms...")
                    
                    # Look for any PDF-related links or buttons
                    pdf_elements = []
                    
                    # Check all links
                    for link in soup.find_all('a', href=True):
                        href = link.get('href', '')
                        text = link.get_text().strip()
                        
                        if any(keyword in href.lower() for keyword in ['pdf', 'download', 'galley', 'view']):
                            pdf_elements.append(('link', href, text))
                    
                    # Check for forms that might handle downloads
                    for form in soup.find_all('form'):
                        action = form.get('action', '')
                        if action:
                            pdf_elements.append(('form', action, 'Form action'))
                    
                    # Check for JavaScript patterns
                    scripts = soup.find_all('script')
                    for script in scripts:
                        if script.string:
                            # Look for URL patterns in JavaScript
                            js_urls = re.findall(r'["\']([^"\']*(?:pdf|download|galley)[^"\']*)["\']', script.string, re.IGNORECASE)
                            for url in js_urls:
                                pdf_elements.append(('javascript', url, 'JS URL'))
                    
                    print(f"   Found {len(pdf_elements)} potential download elements:")
                    for elem_type, url, text in pdf_elements[:10]:  # Show first 10
                        print(f"     [{elem_type}] {text[:50]} -> {url}")
                    
                    # Test the most promising URLs
                    print(f"\n   Testing discovered URLs:")
                    for elem_type, url, text in pdf_elements[:5]:  # Test first 5
                        if url.startswith('/'):
                            full_url = f"https://www.jstatsoft.org{url}"
                        elif not url.startswith('http'):
                            full_url = f"https://www.jstatsoft.org/{url}"
                        else:
                            full_url = url
                        
                        try:
                            async with session.head(full_url, allow_redirects=True) as test_response:
                                ct = test_response.headers.get('content-type', '')
                                cl = test_response.headers.get('content-length', 'unknown')
                                
                                print(f"     {full_url}")
                                print(f"       Status: {test_response.status}, Type: {ct}, Size: {cl}")
                                
                                if test_response.status == 200 and 'pdf' in ct.lower():
                                    print(f"       ✓ SUCCESS! This is a working PDF URL!")
                                    return full_url.replace('v114i01', '{article_id}')
                                
                        except Exception as e:
                            print(f"       Error: {e}")
                        
                        await asyncio.sleep(0.5)
        
        except Exception as e:
            print(f"   Error analyzing article page: {e}")
        
        # Step 2: Try systematic URL pattern testing
        print(f"\n2. Systematic URL pattern testing...")
        
        # Test with known article IDs
        test_articles = ['v114i01', 'v113i01', 'v112i01']  # Recent volumes
        
        # Comprehensive URL patterns based on common academic publishing systems
        url_patterns = [
            # OJS (Open Journal Systems) patterns
            "https://www.jstatsoft.org/index.php/jss/article/view/{article_id}/pdf",
            "https://www.jstatsoft.org/index.php/jss/article/download/{article_id}/pdf",
            "https://www.jstatsoft.org/index.php/jss/article/viewPDF/{article_id}",
            "https://www.jstatsoft.org/index.php/jss/article/viewFile/{article_id}/pdf",
            
            # Direct patterns
            "https://www.jstatsoft.org/article/view/{article_id}/pdf",
            "https://www.jstatsoft.org/article/download/{article_id}/pdf",
            "https://www.jstatsoft.org/article/viewPDF/{article_id}",
            "https://www.jstatsoft.org/article/viewFile/{article_id}/pdf",
            
            # Galley patterns (common in OJS)
            "https://www.jstatsoft.org/index.php/jss/article/view/{article_id}/galley/pdf",
            "https://www.jstatsoft.org/index.php/jss/article/download/{article_id}/galley/pdf",
            "https://www.jstatsoft.org/article/view/{article_id}/galley/pdf",
            "https://www.jstatsoft.org/article/download/{article_id}/galley/pdf",
            
            # File ID patterns
            "https://www.jstatsoft.org/index.php/jss/article/viewFile/{article_id}/0",
            "https://www.jstatsoft.org/index.php/jss/article/viewFile/{article_id}/1",
            "https://www.jstatsoft.org/index.php/jss/article/download/{article_id}/0",
            "https://www.jstatsoft.org/index.php/jss/article/download/{article_id}/1",
            
            # Gateway patterns
            "https://www.jstatsoft.org/index.php/jss/gateway/plugin/WebFeedGatewayPlugin/pdf/{article_id}",
            "https://www.jstatsoft.org/gateway/plugin/WebFeedGatewayPlugin/pdf/{article_id}",
            
            # Alternative formats
            "https://www.jstatsoft.org/index.php/jss/rt/printerFriendly/{article_id}/0",
            "https://www.jstatsoft.org/rt/printerFriendly/{article_id}/0",
        ]
        
        working_patterns = []
        
        for article_id in test_articles:
            print(f"\n   Testing with article: {article_id}")
            
            for i, pattern in enumerate(url_patterns):
                url = pattern.format(article_id=article_id)
                
                try:
                    async with session.get(url, allow_redirects=True) as response:
                        ct = response.headers.get('content-type', '')
                        cl = response.headers.get('content-length', 'unknown')
                        
                        print(f"     Pattern {i+1:2d}: Status {response.status}, Type: {ct[:30]}")
                        
                        if response.status == 200:
                            # Check if it's actually a PDF
                            content = await response.read()
                            
                            if content.startswith(b'%PDF'):
                                print(f"       ✓ SUCCESS! Working PDF pattern found!")
                                print(f"       URL: {url}")
                                print(f"       Size: {len(content)} bytes")
                                
                                pattern_template = pattern.replace(article_id, '{article_id}')
                                if pattern_template not in working_patterns:
                                    working_patterns.append(pattern_template)
                                
                                # Test with another article to confirm
                                if len(test_articles) > 1:
                                    test_url = pattern.format(article_id=test_articles[1])
                                    try:
                                        async with session.head(test_url) as confirm_response:
                                            if confirm_response.status == 200:
                                                print(f"       ✓ Confirmed working with {test_articles[1]}")
                                            else:
                                                print(f"       ⚠ May not work for all articles ({confirm_response.status})")
                                    except:
                                        pass
                            
                            elif len(content) < 1000 and b'<html' in content[:500]:
                                print(f"       → HTML page (possibly error or redirect)")
                            else:
                                print(f"       → Unknown content type, size: {len(content)}")
                        
                        elif response.status in [301, 302, 303, 307, 308]:
                            location = response.headers.get('location', '')
                            print(f"       → Redirects to: {location}")
                        
                except Exception as e:
                    print(f"       Error: {e}")
                
                await asyncio.sleep(0.3)  # Rate limiting
            
            # Don't test all articles with all patterns if we found working ones
            if working_patterns:
                break
        
        print(f"\n=== RESULTS ===")
        if working_patterns:
            print(f"Found {len(working_patterns)} working JSS patterns:")
            for i, pattern in enumerate(working_patterns, 1):
                print(f"  {i}. {pattern}")
        else:
            print("No working JSS patterns found.")
            print("JSS may require:")
            print("  - Authentication/login")
            print("  - Specific referrer headers")
            print("  - JavaScript execution")
            print("  - Different access method")
        
        return working_patterns

async def test_jss_with_different_headers():
    """Test JSS with different header combinations."""
    
    print(f"\n3. Testing with different header combinations...")
    
    header_sets = [
        # Standard browser headers
        {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/pdf,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none'
        },
        # With referrer from JSS site
        {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/pdf,*/*',
            'Referer': 'https://www.jstatsoft.org/article/view/v114i01',
            'Accept-Language': 'en-US,en;q=0.9'
        },
        # Academic crawler headers
        {
            'User-Agent': 'Mozilla/5.0 (compatible; academic-crawler/1.0; +https://example.com/bot)',
            'Accept': 'application/pdf,*/*',
            'From': 'researcher@example.com'
        }
    ]
    
    test_url = "https://www.jstatsoft.org/index.php/jss/article/viewFile/v114i01/0"
    
    for i, headers in enumerate(header_sets, 1):
        print(f"   Header set {i}:")
        
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                async with session.get(test_url, allow_redirects=True) as response:
                    ct = response.headers.get('content-type', '')
                    cl = response.headers.get('content-length', 'unknown')
                    
                    print(f"     Status: {response.status}, Type: {ct}, Size: {cl}")
                    
                    if response.status == 200:
                        content = await response.read()
                        if content.startswith(b'%PDF'):
                            print(f"     ✓ SUCCESS! PDF downloaded with these headers")
                            return headers
                        else:
                            print(f"     Content preview: {content[:100]}")
        
        except Exception as e:
            print(f"     Error: {e}")
        
        await asyncio.sleep(1)
    
    return None

async def main():
    """Main test function."""
    print("JSS Comprehensive Pattern Testing")
    print("=" * 50)
    
    working_patterns = await find_working_jss_patterns()
    working_headers = await test_jss_with_different_headers()
    
    print(f"\n" + "=" * 50)
    print("FINAL RECOMMENDATIONS:")
    
    if working_patterns:
        print(f"\nWorking URL patterns:")
        for pattern in working_patterns:
            print(f"  - {pattern}")
    
    if working_headers:
        print(f"\nWorking headers:")
        for key, value in working_headers.items():
            print(f"  {key}: {value}")
    
    if not working_patterns and not working_headers:
        print("\nNo working patterns found. JSS may require:")
        print("  1. User authentication/login")
        print("  2. Institution-based access")
        print("  3. Different access method (API, etc.)")
        print("  4. Manual download process")

if __name__ == "__main__":
    asyncio.run(main())