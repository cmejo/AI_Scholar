#!/usr/bin/env python3
"""
Test redirects to find actual working URLs
"""

import asyncio
import aiohttp

async def follow_jss_redirects():
    """Follow JSS redirects to find actual PDF URLs."""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        
        print("Following JSS redirects...")
        
        # Test the patterns that returned redirects
        redirect_patterns = [
            "https://www.jstatsoft.org/index.php/jss/article/viewFile/v114i01/0",
            "https://www.jstatsoft.org/index.php/jss/article/viewFile/v114i01/1",
            "https://www.jstatsoft.org/article/viewFile/v114i01/0",
            "https://www.jstatsoft.org/article/viewFile/v114i01/1",
            "https://www.jstatsoft.org/index.php/jss/gateway/plugin/WebFeedGatewayPlugin/pdf/v114i01",
            "https://www.jstatsoft.org/gateway/plugin/WebFeedGatewayPlugin/pdf/v114i01",
        ]
        
        for pattern in redirect_patterns:
            print(f"\nTesting: {pattern}")
            
            try:
                # Follow redirects manually to see the chain
                current_url = pattern
                redirect_chain = []
                
                for i in range(5):  # Max 5 redirects
                    async with session.get(current_url, allow_redirects=False) as response:
                        print(f"  Step {i+1}: Status {response.status}")
                        print(f"    URL: {current_url}")
                        print(f"    Content-Type: {response.headers.get('content-type', 'unknown')}")
                        
                        if response.status in [301, 302, 303, 307, 308]:
                            location = response.headers.get('location', '')
                            if location:
                                if location.startswith('/'):
                                    current_url = f"https://www.jstatsoft.org{location}"
                                elif not location.startswith('http'):
                                    current_url = f"https://www.jstatsoft.org/{location}"
                                else:
                                    current_url = location
                                
                                redirect_chain.append(current_url)
                                print(f"    Redirects to: {current_url}")
                            else:
                                print(f"    No location header found")
                                break
                        elif response.status == 200:
                            ct = response.headers.get('content-type', '')
                            cl = response.headers.get('content-length', 'unknown')
                            
                            if 'pdf' in ct.lower():
                                print(f"    ✓ SUCCESS! Found PDF")
                                print(f"    Content-Length: {cl}")
                                
                                # Test download
                                content = await response.read()
                                if content.startswith(b'%PDF'):
                                    print(f"    ✓ Confirmed valid PDF ({len(content)} bytes)")
                                else:
                                    print(f"    ⚠ Content doesn't start with PDF header")
                            else:
                                print(f"    Final content type: {ct}")
                                if ct == 'text/html':
                                    content = await response.text()
                                    if len(content) < 1000:
                                        print(f"    Content preview: {content[:200]}...")
                            break
                        else:
                            print(f"    Error status: {response.status}")
                            break
                    
                    await asyncio.sleep(0.5)
                
                if redirect_chain:
                    print(f"  Redirect chain: {' -> '.join(redirect_chain)}")
                    
            except Exception as e:
                print(f"  Error: {e}")
            
            await asyncio.sleep(1)

async def test_rjournal_article_pages():
    """Test R Journal article pages to find PDF links."""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        
        print("\nTesting R Journal article pages...")
        
        # Test some known R Journal article patterns
        test_articles = [
            "https://journal.r-project.org/articles/RJ-2023-048/",
            "https://journal.r-project.org/articles/RJ-2022-048/", 
            "https://journal.r-project.org/articles/RJ-2021-048/",
        ]
        
        for article_url in test_articles:
            print(f"\nTesting: {article_url}")
            
            try:
                async with session.get(article_url) as response:
                    print(f"  Status: {response.status}")
                    
                    if response.status == 200:
                        content = await response.text()
                        
                        if content.startswith('%PDF'):
                            print(f"  ✓ This is a PDF! Size: {len(content)} bytes")
                        else:
                            print(f"  This is HTML, looking for PDF links...")
                            
                            from bs4 import BeautifulSoup
                            soup = BeautifulSoup(content, 'html.parser')
                            
                            # Look for PDF links
                            pdf_found = False
                            for link in soup.find_all('a', href=True):
                                href = link.get('href', '')
                                text = link.get_text().strip()
                                
                                if 'pdf' in href.lower() or 'pdf' in text.lower():
                                    full_url = href if href.startswith('http') else f"https://journal.r-project.org{href}"
                                    print(f"    PDF link: {text} -> {full_url}")
                                    pdf_found = True
                                    
                                    # Test the PDF link
                                    try:
                                        async with session.head(full_url) as pdf_response:
                                            ct = pdf_response.headers.get('content-type', '')
                                            cl = pdf_response.headers.get('content-length', 'unknown')
                                            print(f"      Status: {pdf_response.status}, Type: {ct}, Size: {cl}")
                                            
                                            if pdf_response.status == 200 and 'pdf' in ct.lower():
                                                print(f"      ✓ Working PDF link!")
                                    except Exception as e:
                                        print(f"      Error testing PDF: {e}")
                                    
                                    await asyncio.sleep(0.5)
                            
                            if not pdf_found:
                                print(f"    No PDF links found in article page")
                    
            except Exception as e:
                print(f"  Error: {e}")
            
            await asyncio.sleep(1)

async def test_direct_rjournal_patterns():
    """Test direct R Journal PDF patterns."""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        
        print("\nTesting direct R Journal PDF patterns...")
        
        # Test different direct PDF patterns
        patterns = [
            "https://journal.r-project.org/articles/RJ-2023-048/RJ-2023-048.pdf",
            "https://journal.r-project.org/archive/2023/RJ-2023-048/RJ-2023-048.pdf",
            "https://journal.r-project.org/issues/2023-2/RJ-2023-048.pdf",
        ]
        
        for pattern in patterns:
            print(f"\nTesting: {pattern}")
            
            try:
                async with session.head(pattern) as response:
                    ct = response.headers.get('content-type', '')
                    cl = response.headers.get('content-length', 'unknown')
                    
                    print(f"  Status: {response.status}")
                    print(f"  Content-Type: {ct}")
                    print(f"  Content-Length: {cl}")
                    
                    if response.status == 200 and 'pdf' in ct.lower():
                        print(f"  ✓ SUCCESS! Working PDF pattern")
                    elif response.status == 200:
                        print(f"  ⚠ Returns content but not PDF")
                    
            except Exception as e:
                print(f"  Error: {e}")
            
            await asyncio.sleep(1)

async def main():
    """Main test function."""
    print("Redirect and Pattern Discovery Test")
    print("=" * 50)
    
    await follow_jss_redirects()
    await test_rjournal_article_pages()
    await test_direct_rjournal_patterns()

if __name__ == "__main__":
    asyncio.run(main())