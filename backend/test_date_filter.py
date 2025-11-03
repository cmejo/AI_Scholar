#!/usr/bin/env python3
"""
Test script to debug date filter format.
"""

import asyncio
import aiohttp
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta


async def test_date_filter():
    """Test different date filter formats."""
    
    api_url = "http://export.arxiv.org/api/query"
    category = "q-fin.CP"  # Use a specific category
    
    # Test different date filter formats
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    date_filters = [
        # Current format from downloader
        f"submittedDate:[{start_date.strftime('%Y%m%d')}0000+TO+{end_date.strftime('%Y%m%d')}2359]",
        
        # Alternative formats
        f"submittedDate:[{start_date.strftime('%Y%m%d')}+TO+{end_date.strftime('%Y%m%d')}]",
        f"lastUpdatedDate:[{start_date.strftime('%Y%m%d')}+TO+{end_date.strftime('%Y%m%d')}]",
        
        # Try with different date format
        f"submittedDate:[{start_date.strftime('%Y-%m-%d')}+TO+{end_date.strftime('%Y-%m-%d')}]",
        
        # Try recent papers without specific date
        "submittedDate:[202510*]",  # October 2025
    ]
    
    async with aiohttp.ClientSession() as session:
        for i, date_filter in enumerate(date_filters):
            print(f"\nTest {i+1}: {date_filter}")
            
            search_query = f"cat:{category}"
            full_query = f"{search_query}+AND+{date_filter}"
            
            params = {
                'search_query': full_query,
                'start': 0,
                'max_results': 5,
                'sortBy': 'submittedDate',
                'sortOrder': 'descending'
            }
            
            try:
                async with session.get(api_url, params=params) as response:
                    print(f"  Status: {response.status}")
                    
                    if response.status == 200:
                        content = await response.text()
                        root = ET.fromstring(content)
                        
                        # Check for errors
                        error_elem = root.find('.//{http://www.w3.org/2005/Atom}error')
                        if error_elem is not None:
                            print(f"  API Error: {error_elem.text}")
                            continue
                        
                        entries = root.findall('.//{http://www.w3.org/2005/Atom}entry')
                        print(f"  Found {len(entries)} papers")
                        
                        if entries:
                            entry = entries[0]
                            published_elem = entry.find('.//{http://www.w3.org/2005/Atom}published')
                            title_elem = entry.find('.//{http://www.w3.org/2005/Atom}title')
                            if published_elem is not None and title_elem is not None:
                                pub_date = published_elem.text
                                title = title_elem.text.strip()[:50]
                                print(f"  First paper: {pub_date} - {title}...")
                    else:
                        print(f"  HTTP Error: {response.status}")
                        
            except Exception as e:
                print(f"  Error: {e}")
            
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(test_date_filter())