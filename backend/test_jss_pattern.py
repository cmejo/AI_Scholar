#!/usr/bin/env python3
"""
Test the discovered JSS pattern more thoroughly
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re

async def analyze_jss_pattern():
    """Analyze the JSS pattern we discovered."""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        
        print("Analyzing JSS Pattern")
        print("=" * 30)
        
        # Test the working pattern we found
        working_url = "https://www.jstatsoft.org/index.php/jss/article/view/v114i01/4752"
        
        print(f"Testing working URL: {working_url}")
        
        try:
            async with session.get(working_url) as response:
                print(f"Status: {response.status}")
                print(f"Content-Type: {response.headers.get('content-type', 'unknown')}")
                print(f"Content-Length: {response.headers.get('content-length', 'unknown')}")
                
                if response.status == 200:
                    content = await response.read()
                    if content.startswith(b'%PDF'):
                        print(f"✓ Confirmed: This is a PDF ({len(content)} bytes)")
                    else:
                        print(f"Content preview: {content[:100]}")
        
        except Exception as e:
            print(f"Error: {e}")
        
        # Now let's understand how to get the file IDs for different articles
        print(f"\nAnalyzing how to get file IDs...")
        
        # Check the article page to see how file IDs are structured
        article_page_url = "https://www.jstatsoft.org/article/view/v114i01"
        
        try:
            async with session.get(article_page_url) as response:
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    print(f"Analyzing article page: {article_page_url}")
                    
                    # Find all links that match the pattern /article/view/v114i01/XXXX
                    file_links = []
                    for link in soup.find_all('a', href=True):
                        href = link.get('href', '')
                        text = link.get_text().strip()
                        
                        # Look for the pattern we discovered
                        if '/article/view/v114i01/' in href and href.split('/')[-1].isdigit():
                            file_id = href.split('/')[-1]
                            file_links.append((file_id, text, href))
                    
                    print(f"Found {len(file_links)} file links:")
                    for file_id, text, href in file_links:
                        print(f"  File ID {file_id}: {text}")
                        
                        # Test each file ID
                        full_url = f"https://www.jstatsoft.org{href}" if href.startswith('/') else href
                        
                        try:
                            async with session.head(full_url) as file_response:
                                ct = file_response.headers.get('content-type', '')
                                cl = file_response.headers.get('content-length', 'unknown')
                                
                                is_pdf = 'pdf' in ct.lower()
                                print(f"    Status: {file_response.status}, Type: {ct}, PDF: {is_pdf}")
                                
                        except Exception as e:
                            print(f"    Error: {e}")
                        
                        await asyncio.sleep(0.5)
        
        except Exception as e:
            print(f"Error analyzing article page: {e}")
        
        # Test with other articles to see if we can find a pattern
        print(f"\nTesting pattern with other articles...")
        
        other_articles = ['v113i01', 'v112i01', 'v111i01']
        
        for article_id in other_articles:
            print(f"\nTesting article: {article_id}")
            
            article_url = f"https://www.jstatsoft.org/article/view/{article_id}"
            
            try:
                async with session.get(article_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        # Find file links for this article
                        file_links = []
                        for link in soup.find_all('a', href=True):
                            href = link.get('href', '')
                            text = link.get_text().strip()
                            
                            if f'/article/view/{article_id}/' in href and href.split('/')[-1].isdigit():
                                file_id = href.split('/')[-1]
                                file_links.append((file_id, text))
                        
                        print(f"  Found {len(file_links)} files:")
                        for file_id, text in file_links[:3]:  # Test first 3
                            print(f"    File ID {file_id}: {text}")
                            
                            # Test if it's a PDF
                            test_url = f"https://www.jstatsoft.org/index.php/jss/article/view/{article_id}/{file_id}"
                            
                            try:
                                async with session.head(test_url) as test_response:
                                    ct = test_response.headers.get('content-type', '')
                                    is_pdf = 'pdf' in ct.lower()
                                    
                                    if is_pdf:
                                        print(f"      ✓ PDF found! URL: {test_url}")
                                    else:
                                        print(f"      Status: {test_response.status}, Type: {ct}")
                            
                            except Exception as e:
                                print(f"      Error: {e}")
                            
                            await asyncio.sleep(0.5)
                    
                    else:
                        print(f"  Article not found: {response.status}")
            
            except Exception as e:
                print(f"  Error: {e}")
            
            await asyncio.sleep(1)

async def main():
    await analyze_jss_pattern()

if __name__ == "__main__":
    asyncio.run(main())