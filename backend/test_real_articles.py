#!/usr/bin/env python3
"""
Test with real article IDs to confirm patterns
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup

async def find_real_jss_articles():
    """Find real JSS article IDs from the current issue."""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        
        print("Finding real JSS articles...")
        
        # Get the current JSS issue
        issue_url = "https://www.jstatsoft.org/index.php/jss/issue/current"
        
        try:
            async with session.get(issue_url) as response:
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    print(f"Checking current JSS issue: {issue_url}")
                    
                    # Find article view links
                    article_ids = []
                    for link in soup.find_all('a', href=True):
                        href = link.get('href', '')
                        if '/article/view/' in href:
                            # Extract article ID
                            parts = href.split('/')
                            if len(parts) > 0:
                                article_id = parts[-1]
                                if article_id and article_id not in article_ids:
                                    article_ids.append(article_id)
                    
                    print(f"Found {len(article_ids)} article IDs: {article_ids[:10]}")
                    
                    # Test the download patterns with real IDs
                    for article_id in article_ids[:3]:  # Test first 3
                        print(f"\nTesting article ID: {article_id}")
                        
                        # Test the pattern we discovered from redirects
                        test_patterns = [
                            f"https://www.jstatsoft.org/article/download/{article_id}/0/0",
                            f"https://www.jstatsoft.org/article/download/{article_id}/1/0",
                            f"https://www.jstatsoft.org/index.php/jss/article/download/{article_id}/0/0",
                            f"https://www.jstatsoft.org/index.php/jss/article/download/{article_id}/1/0",
                        ]
                        
                        for pattern in test_patterns:
                            try:
                                async with session.head(pattern) as test_response:
                                    ct = test_response.headers.get('content-type', '')
                                    cl = test_response.headers.get('content-length', 'unknown')
                                    
                                    print(f"  {pattern}")
                                    print(f"    Status: {test_response.status}, Type: {ct}, Size: {cl}")
                                    
                                    if test_response.status == 200 and 'pdf' in ct.lower():
                                        print(f"    ✓ SUCCESS! Working JSS pattern")
                                        return pattern.replace(article_id, '{article_id}')
                                    
                            except Exception as e:
                                print(f"    Error: {e}")
                            
                            await asyncio.sleep(0.5)
                        
        except Exception as e:
            print(f"Error: {e}")
    
    return None

async def find_real_rjournal_articles():
    """Find real R Journal article IDs."""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        
        print("\nFinding real R Journal articles...")
        
        # Get recent R Journal issues
        issues_url = "https://journal.r-project.org/issues.html"
        
        try:
            async with session.get(issues_url) as response:
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    print(f"Checking R Journal issues: {issues_url}")
                    
                    # Find recent issue links
                    issue_links = []
                    for link in soup.find_all('a', href=True):
                        href = link.get('href', '')
                        text = link.get_text().strip()
                        
                        if 'issues/' in href and any(year in href for year in ['2023', '2024', '2025']):
                            full_url = href if href.startswith('http') else f"https://journal.r-project.org/{href}"
                            issue_links.append((full_url, text))
                    
                    print(f"Found {len(issue_links)} recent issues")
                    
                    # Check the most recent issue
                    if issue_links:
                        issue_url, issue_text = issue_links[0]
                        print(f"\nChecking issue: {issue_text} -> {issue_url}")
                        
                        async with session.get(issue_url) as issue_response:
                            if issue_response.status == 200:
                                issue_content = await issue_response.text()
                                issue_soup = BeautifulSoup(issue_content, 'html.parser')
                                
                                # Find article IDs
                                article_ids = []
                                for link in issue_soup.find_all('a', href=True):
                                    href = link.get('href', '')
                                    
                                    # Look for RJ-YYYY-NNN pattern
                                    if 'RJ-' in href:
                                        import re
                                        match = re.search(r'RJ-\d{4}-\d{3}', href)
                                        if match:
                                            article_id = match.group()
                                            if article_id not in article_ids:
                                                article_ids.append(article_id)
                                
                                print(f"Found {len(article_ids)} article IDs: {article_ids[:10]}")
                                
                                # Test the working pattern with real IDs
                                for article_id in article_ids[:3]:  # Test first 3
                                    print(f"\nTesting R Journal article: {article_id}")
                                    
                                    test_url = f"https://journal.r-project.org/articles/{article_id}/{article_id}.pdf"
                                    
                                    try:
                                        async with session.head(test_url) as test_response:
                                            ct = test_response.headers.get('content-type', '')
                                            cl = test_response.headers.get('content-length', 'unknown')
                                            
                                            print(f"  {test_url}")
                                            print(f"    Status: {test_response.status}, Type: {ct}, Size: {cl}")
                                            
                                            if test_response.status == 200 and 'pdf' in ct.lower():
                                                print(f"    ✓ SUCCESS! Confirmed working R Journal pattern")
                                            
                                    except Exception as e:
                                        print(f"    Error: {e}")
                                    
                                    await asyncio.sleep(0.5)
                        
        except Exception as e:
            print(f"Error: {e}")

async def main():
    """Main test function."""
    print("Real Article ID Test")
    print("=" * 50)
    
    jss_pattern = await find_real_jss_articles()
    await find_real_rjournal_articles()
    
    print(f"\nResults:")
    print(f"JSS working pattern: {jss_pattern or 'Not found'}")
    print(f"R Journal working pattern: https://journal.r-project.org/articles/{{article_id}}/{{article_id}}.pdf")

if __name__ == "__main__":
    asyncio.run(main())