#!/usr/bin/env python3
"""
Test exact date ranges that should work.
"""

import asyncio
import aiohttp
import xml.etree.ElementTree as ET


async def test_exact_dates():
    """Test with exact date ranges that should capture recent papers."""
    
    api_url = "http://export.arxiv.org/api/query"
    
    # Test different date ranges that should capture papers from 20251022-20251030
    test_queries = [
        # Should capture recent papers
        "cat:q-fin.CP+AND+submittedDate:[20251020+TO+20251031]",
        "cat:q-fin.CP+AND+submittedDate:[202510*]",
        "cat:q-fin.CP+AND+submittedDate:[2025*]",
        
        # Try without the +AND+ syntax
        "cat:q-fin.CP submittedDate:[20251020+TO+20251031]",
        
        # Try with different field
        "cat:q-fin.CP+AND+lastUpdatedDate:[20251020+TO+20251031]",
        
        # Just the category (should work)
        "cat:q-fin.CP",
    ]
    
    async with aiohttp.ClientSession() as session:
        for i, query in enumerate(test_queries):
            print(f"\nTest {i+1}: {query}")
            
            params = {
                'search_query': query,
                'start': 0,
                'max_results': 3,
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
                        
                        for j, entry in enumerate(entries):
                            published_elem = entry.find('.//{http://www.w3.org/2005/Atom}published')
                            id_elem = entry.find('.//{http://www.w3.org/2005/Atom}id')
                            if published_elem is not None and id_elem is not None:
                                pub_date = published_elem.text
                                paper_id = id_elem.text.split('/')[-1]
                                print(f"    {j+1}. {paper_id} - {pub_date}")
                    else:
                        print(f"  HTTP Error: {response.status}")
                        
            except Exception as e:
                print(f"  Error: {e}")
            
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(test_exact_dates())