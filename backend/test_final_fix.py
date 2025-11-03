#!/usr/bin/env python3
"""
Test the final fixes to the quant scholar downloader.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from multi_instance_arxiv_system.scripts.quant_scholar_downloader import QuantScholarDownloader


async def test_final_fix():
    """Test the final fixes."""
    
    print("Testing final fixes...")
    
    downloader = QuantScholarDownloader()
    
    # Test with "all" date range and small limits
    stats = await downloader.download_papers(
        sources=["arxiv", "jss", "rjournal"],
        categories=["q-fin.CP"],  # Just one category for testing
        date_range="all",
        max_papers=2,  # Small limit for testing
        dry_run=True
    )
    
    print("\nTest Results:")
    print("=" * 40)
    print(f"Total discovered: {stats['total_discovered']}")
    print(f"Duration: {stats['duration_minutes']:.1f} minutes")
    
    for source, source_stats in stats['source_stats'].items():
        print(f"\n{source.upper()}:")
        print(f"  Discovered: {source_stats.get('discovered', 0)}")
        print(f"  Downloaded: {source_stats.get('downloaded', 0)}")
        print(f"  Failed: {source_stats.get('failed', 0)}")
    
    if stats['total_discovered'] > 0:
        print("\n✅ Fix successful - papers discovered!")
    else:
        print("\n❌ Still not working")


if __name__ == "__main__":
    asyncio.run(test_final_fix())