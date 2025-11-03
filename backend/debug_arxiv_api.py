#!/usr/bin/env python3
"""
Debug script to test arXiv API directly.
"""

import asyncio
import aiohttp
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta


async def test_arxiv_api():
    """Test arXiv API with different queries."""
    
    print("Testing arXiv API...")
    
    # Test queries
    queries = [
        "cat:q-fin*",  # Wildcard query
        "cat:q-fin.CP",  # Specific category
        "cat:stat.ML",  # Machine learning stats
        "all:machine learning",  # General search
    ]
    
    api_url = "http://export.arxiv.org/api/query"
    
    async with aiohttp.ClientSession() as session:
        for query in queries:
            print(f"\nTesting query: {query}")
            
            params = {
                'search_query': query,
                'start': 0,
                'max_results': 5,
                'sortBy': 'submittedDate',
                'sortOrder': 'descending'
            }
            
            try:
                async with session.get(api_url, params=params) as response:
                    print(f"Status: {response.status}")
                    
                    if response.status == 200:
                        content = await response.text()
                        
                        # Parse XML
                        root = ET.fromstring(content)
                        
                        # Check for errors
                        error_elem = root.find('.//{http://www.w3.org/2005/Atom}error')
                        if error_elem is not None:
                            print(f"API Error: {error_elem.text}")
                            continue
                        
                        # Count entries
                        entries = root.findall('.//{http://www.w3.org/2005/Atom}entry')
                        print(f"Found {len(entries)} papers")
                        
                        # Show first paper details
                        if entries:
                            entry = entries[0]
                            title_elem = entry.find('.//{http://www.w3.org/2005/Atom}title')
                            id_elem = entry.find('.//{http://www.w3.org/2005/Atom}id')
                            
                            if title_elem is not None and id_elem is not None:
                                title = title_elem.text.strip()
                                paper_id = id_elem.text.split('/')[-1]
                                print(f"First paper: {paper_id} - {title[:100]}...")
                    else:
                        print(f"HTTP Error: {response.status}")
                        
            except Exception as e:
                print(f"Error: {e}")
            
            await asyncio.sleep(1)  # Rate limiting


if __name__ == "__main__":
    asyncio.run(test_arxiv_api())