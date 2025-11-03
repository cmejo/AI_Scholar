#!/usr/bin/env python3
"""
Check actual arXiv paper dates to understand the format.
"""

import asyncio
import aiohttp
import xml.etree.ElementTree as ET
from datetime import datetime


async def check_arxiv_dates():
    """Check actual dates in arXiv papers."""
    
    api_url = "http://export.arxiv.org/api/query"
    
    # Get recent papers without date filter
    params = {
        'search_query': 'cat:q-fin.CP',
        'start': 0,
        'max_results': 10,
        'sortBy': 'submittedDate',
        'sortOrder': 'descending'
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(api_url, params=params) as response:
            if response.status == 200:
                content = await response.text()
                root = ET.fromstring(content)
                
                entries = root.findall('.//{http://www.w3.org/2005/Atom}entry')
                print(f"Found {len(entries)} papers")
                
                for i, entry in enumerate(entries):
                    # Get all date fields
                    published_elem = entry.find('.//{http://www.w3.org/2005/Atom}published')
                    updated_elem = entry.find('.//{http://www.w3.org/2005/Atom}updated')
                    title_elem = entry.find('.//{http://www.w3.org/2005/Atom}title')
                    id_elem = entry.find('.//{http://www.w3.org/2005/Atom}id')
                    
                    if published_elem is not None:
                        published = published_elem.text
                        updated = updated_elem.text if updated_elem is not None else "N/A"
                        title = title_elem.text.strip()[:50] if title_elem is not None else "N/A"
                        paper_id = id_elem.text.split('/')[-1] if id_elem is not None else "N/A"
                        
                        print(f"\nPaper {i+1}: {paper_id}")
                        print(f"  Title: {title}...")
                        print(f"  Published: {published}")
                        print(f"  Updated: {updated}")
                        
                        # Parse the date to see the format
                        try:
                            pub_dt = datetime.fromisoformat(published.replace('Z', '+00:00'))
                            print(f"  Parsed date: {pub_dt}")
                            print(f"  Date format for arXiv: {pub_dt.strftime('%Y%m%d')}")
                        except Exception as e:
                            print(f"  Date parsing error: {e}")


if __name__ == "__main__":
    asyncio.run(check_arxiv_dates())