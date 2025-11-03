#!/usr/bin/env python3
"""
Test script to check if the arXiv categories have recent papers.
"""

import asyncio
import aiohttp
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta


async def test_category_papers():
    """Test if specific categories have papers."""
    
    # Categories from the downloader
    categories = [
        "econ.EM", "econ.GN", "econ.TH", "eess.SY", "math.ST", 
        "math.PR", "math.OC", "q-fin.*", "stat.*"
    ]
    
    api_url = "http://export.arxiv.org/api/query"
    
    async with aiohttp.ClientSession() as session:
        for category in categories:
            print(f"\nTesting category: {category}")
            
            # Build query like the downloader does
            if category.endswith('.*'):
                base_cat = category[:-2]
                search_query = f"cat:{base_cat}*"
            else:
                search_query = f"cat:{category}"
            
            # Test without date filter first
            params = {
                'search_query': search_query,
                'start': 0,
                'max_results': 5,
                'sortBy': 'submittedDate',
                'sortOrder': 'descending'
            }
            
            try:
                async with session.get(api_url, params=params) as response:
                    if response.status == 200:
                        content = await response.text()
                        root = ET.fromstring(content)
                        
                        # Check for errors
                        error_elem = root.find('.//{http://www.w3.org/2005/Atom}error')
                        if error_elem is not None:
                            print(f"  API Error: {error_elem.text}")
                            continue
                        
                        entries = root.findall('.//{http://www.w3.org/2005/Atom}entry')
                        print(f"  Found {len(entries)} papers (no date filter)")
                        
                        if entries:
                            # Show most recent paper date
                            entry = entries[0]
                            published_elem = entry.find('.//{http://www.w3.org/2005/Atom}published')
                            if published_elem is not None:
                                pub_date = published_elem.text
                                print(f"  Most recent: {pub_date}")
                        
                        # Now test with recent date filter
                        end_date = datetime.now()
                        start_date = end_date - timedelta(days=30)
                        date_filter = f"submittedDate:[{start_date.strftime('%Y%m%d')}0000+TO+{end_date.strftime('%Y%m%d')}2359]"
                        full_query = f"{search_query}+AND+{date_filter}"
                        
                        params['search_query'] = full_query
                        
                        async with session.get(api_url, params=params) as response2:
                            if response2.status == 200:
                                content2 = await response2.text()
                                root2 = ET.fromstring(content2)
                                entries2 = root2.findall('.//{http://www.w3.org/2005/Atom}entry')
                                print(f"  Found {len(entries2)} papers (last 30 days)")
                    else:
                        print(f"  HTTP Error: {response.status}")
                        
            except Exception as e:
                print(f"  Error: {e}")
            
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(test_category_papers())