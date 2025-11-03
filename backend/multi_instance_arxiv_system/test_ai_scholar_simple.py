#!/usr/bin/env python3
"""
Simple test for AI Scholar Downloader components.

Tests individual components without requiring full infrastructure.
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_arxiv_api_client():
    """Test arXiv API client functionality."""
    logger.info("Testing arXiv API client...")
    
    try:
        # Import the ArxivAPIClient directly
        sys.path.append(str(Path(__file__).parent))
        
        # Create a minimal version for testing
        import xml.etree.ElementTree as ET
        import aiohttp
        from urllib.parse import urlencode
        import time
        
        class TestArxivAPIClient:
            """Simplified arXiv API client for testing."""
            
            def __init__(self):
                self.base_url = "http://export.arxiv.org/api/query"
                self.rate_limit_delay = 3.0
                self.last_request_time = 0
                
            async def _rate_limit(self):
                """Enforce rate limiting between API requests."""
                current_time = time.time()
                time_since_last = current_time - self.last_request_time
                
                if time_since_last < self.rate_limit_delay:
                    sleep_time = self.rate_limit_delay - time_since_last
                    await asyncio.sleep(sleep_time)
                
                self.last_request_time = time.time()
            
            async def test_search(self, category: str = "quant-ph", max_results: int = 5):
                """Test search functionality."""
                await self._rate_limit()
                
                query_params = {
                    'search_query': f'cat:{category}',
                    'start': 0,
                    'max_results': max_results,
                    'sortBy': 'submittedDate',
                    'sortOrder': 'descending'
                }
                
                async with aiohttp.ClientSession() as session:
                    url = f"{self.base_url}?{urlencode(query_params)}"
                    
                    async with session.get(url) as response:
                        if response.status != 200:
                            logger.error(f"API request failed: {response.status}")
                            return []
                        
                        content = await response.text()
                        return self._parse_response(content)
            
            def _parse_response(self, xml_content: str):
                """Parse arXiv API XML response."""
                papers = []
                
                try:
                    root = ET.fromstring(xml_content)
                    
                    # Define namespaces
                    namespaces = {
                        'atom': 'http://www.w3.org/2005/Atom',
                        'arxiv': 'http://arxiv.org/schemas/atom'
                    }
                    
                    entries = root.findall('atom:entry', namespaces)
                    
                    for entry in entries:
                        try:
                            # Extract basic information
                            arxiv_id = entry.find('atom:id', namespaces).text.split('/')[-1]
                            title = entry.find('atom:title', namespaces).text.strip()
                            
                            # Extract authors
                            authors = []
                            author_elements = entry.findall('atom:author', namespaces)
                            for author_elem in author_elements:
                                name_elem = author_elem.find('atom:name', namespaces)
                                if name_elem is not None:
                                    authors.append(name_elem.text.strip())
                            
                            papers.append({
                                'arxiv_id': arxiv_id,
                                'title': title,
                                'authors': authors[:3]  # First 3 authors
                            })
                            
                        except Exception as e:
                            logger.error(f"Failed to parse entry: {e}")
                            continue
                            
                except Exception as e:
                    logger.error(f"Failed to parse XML response: {e}")
                
                return papers
        
        # Test the client
        client = TestArxivAPIClient()
        papers = await client.test_search(category="quant-ph", max_results=3)
        
        logger.info(f"ArXiv API test: Found {len(papers)} papers")
        
        for i, paper in enumerate(papers):
            logger.info(f"Paper {i+1}: {paper['title'][:80]}...")
            logger.info(f"  ArXiv ID: {paper['arxiv_id']}")
            logger.info(f"  Authors: {', '.join(paper['authors'])}")
        
        return len(papers) > 0
        
    except Exception as e:
        logger.error(f"ArXiv API client test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_config_loading():
    """Test configuration loading."""
    logger.info("Testing configuration loading...")
    
    try:
        import yaml
        
        config_path = Path(__file__).parent / "configs" / "ai_scholar.yaml"
        
        if not config_path.exists():
            logger.error(f"Config file not found: {config_path}")
            return False
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        logger.info(f"Loaded config for instance: {config['instance']['name']}")
        logger.info(f"ArXiv categories: {config['data_sources']['arxiv']['categories']}")
        logger.info(f"Storage paths configured: {len(config['storage'])}")
        
        return True
        
    except Exception as e:
        logger.error(f"Config loading test failed: {e}")
        return False


async def test_directory_creation():
    """Test directory creation functionality."""
    logger.info("Testing directory creation...")
    
    try:
        import yaml
        
        config_path = Path(__file__).parent / "configs" / "ai_scholar.yaml"
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Test creating directories (in a test subdirectory)
        test_base = Path(__file__).parent / "test_storage"
        
        directories = [
            test_base / "pdf",
            test_base / "processed", 
            test_base / "state",
            test_base / "errors",
            test_base / "archive"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {directory}")
        
        # Clean up test directories
        import shutil
        if test_base.exists():
            shutil.rmtree(test_base)
            logger.info("Cleaned up test directories")
        
        return True
        
    except Exception as e:
        logger.error(f"Directory creation test failed: {e}")
        return False


async def main():
    """Main test function."""
    logger.info("Starting AI Scholar Downloader component tests")
    
    tests = [
        ("Configuration Loading", test_config_loading),
        ("Directory Creation", test_directory_creation),
        ("ArXiv API Client", test_arxiv_api_client),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Running {test_name} Test ---")
        try:
            result = await test_func()
            results.append((test_name, result))
            status = "PASSED" if result else "FAILED"
            logger.info(f"{test_name} Test: {status}")
        except Exception as e:
            logger.error(f"{test_name} Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n--- Test Summary ---")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("All tests completed successfully!")
    else:
        logger.error("Some tests failed!")


if __name__ == "__main__":
    asyncio.run(main())