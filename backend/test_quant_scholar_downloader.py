#!/usr/bin/env python3
"""
Test script for the Quant Scholar Downloader fixes.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from multi_instance_arxiv_system.scripts.quant_scholar_downloader import QuantScholarDownloader


async def test_downloader():
    """Test the fixed downloader with small limits."""
    
    print("Testing Quant Scholar Downloader fixes...")
    
    downloader = QuantScholarDownloader()
    
    # Test with very small limits to verify functionality
    stats = await downloader.download_papers(
        sources=["arxiv", "jss", "rjournal"],
        date_range="last-month",
        max_papers=5,  # Small limit for testing
        dry_run=True,  # Don't actually download
        resume=False
    )
    
    print("\nTest Results:")
    print("=" * 40)
    print(f"Total discovered: {stats['total_discovered']}")
    print(f"Sources processed: {stats['sources_processed']}")
    print(f"Duration: {stats['duration_minutes']:.1f} minutes")
    
    for source, source_stats in stats['source_stats'].items():
        print(f"\n{source.upper()}:")
        print(f"  Discovered: {source_stats.get('discovered', 0)}")
        print(f"  Downloaded: {source_stats.get('downloaded', 0)}")
        print(f"  Failed: {source_stats.get('failed', 0)}")
    
    # Check if all sources found papers
    success = True
    for source in ["arxiv", "jss", "rjournal"]:
        if source in stats['source_stats']:
            discovered = stats['source_stats'][source].get('discovered', 0)
            if discovered == 0:
                print(f"WARNING: No papers discovered from {source}")
                success = False
        else:
            print(f"ERROR: {source} not processed")
            success = False
    
    if success:
        print("\n✅ All sources successfully discovered papers!")
    else:
        print("\n❌ Some sources failed to discover papers")
    
    return success


if __name__ == "__main__":
    success = asyncio.run(test_downloader())
    sys.exit(0 if success else 1)