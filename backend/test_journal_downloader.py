#!/usr/bin/env python3
"""
Test script for journal paper discovery and download
"""

import asyncio
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from multi_instance_arxiv_system.scripts.quant_scholar_downloader import QuantScholarDownloader
from datetime import datetime, timedelta, timezone

async def test_journal_discovery():
    """Test journal paper discovery without downloading."""
    
    downloader = QuantScholarDownloader()
    
    # Test date range
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=30)
    
    print("Testing Journal Paper Discovery")
    print("=" * 50)
    
    # Test JSS discovery
    print("\n1. Testing JSS Discovery...")
    try:
        jss_papers = await downloader._discover_jss_papers(start_date, end_date, max_papers=5)
        print(f"   Found {len(jss_papers)} JSS papers")
        for paper in jss_papers[:3]:  # Show first 3
            print(f"   - {paper['title']}")
            print(f"     URL: {paper['pdf_url']}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test R Journal discovery
    print("\n2. Testing R Journal Discovery...")
    try:
        rjournal_papers = await downloader._discover_rjournal_papers(start_date, end_date, max_papers=5)
        print(f"   Found {len(rjournal_papers)} R Journal papers")
        for paper in rjournal_papers[:3]:  # Show first 3
            print(f"   - {paper['title']}")
            print(f"     URL: {paper['pdf_url']}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test arXiv discovery (small sample)
    print("\n3. Testing arXiv Discovery (small sample)...")
    try:
        arxiv_papers = await downloader._discover_arxiv_papers("q-fin.ST", start_date, end_date, max_papers=3)
        print(f"   Found {len(arxiv_papers)} arXiv papers")
        for paper in arxiv_papers[:2]:  # Show first 2
            print(f"   - {paper['title']}")
            print(f"     URL: {paper['pdf_url']}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\nDiscovery test completed!")

async def test_single_download():
    """Test downloading a single arXiv paper."""
    
    downloader = QuantScholarDownloader()
    
    # Create a test paper (real arXiv paper)
    test_paper = {
        'id': 'test_arxiv_2301.00001',
        'title': 'Test arXiv Paper',
        'source': 'arxiv',
        'pdf_url': 'https://arxiv.org/pdf/2301.00001.pdf'  # This should be a real paper
    }
    
    print("\nTesting Single Paper Download")
    print("=" * 50)
    print(f"Attempting to download: {test_paper['title']}")
    print(f"URL: {test_paper['pdf_url']}")
    
    try:
        success = await downloader._download_paper(test_paper, resume=False)
        if success:
            print("✓ Download successful!")
            
            # Check if file exists
            pdf_path = Path(downloader.pdf_directory) / f"{test_paper['id']}.pdf"
            if pdf_path.exists():
                size = pdf_path.stat().st_size
                print(f"  File size: {size} bytes")
            else:
                print("  Warning: PDF file not found after download")
        else:
            print("✗ Download failed")
    except Exception as e:
        print(f"✗ Download error: {e}")

if __name__ == "__main__":
    print("Journal Downloader Test Suite")
    print("=" * 50)
    
    # Run discovery test
    asyncio.run(test_journal_discovery())
    
    # Ask user if they want to test download
    response = input("\nDo you want to test a single paper download? (y/n): ")
    if response.lower().startswith('y'):
        asyncio.run(test_single_download())
    
    print("\nTest completed!")