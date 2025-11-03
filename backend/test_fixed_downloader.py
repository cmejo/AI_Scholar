#!/usr/bin/env python3
"""
Test the fixed downloader.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from multi_instance_arxiv_system.scripts.quant_scholar_downloader import QuantScholarDownloader


async def test_fixed_downloader():
    """Test the fixed downloader."""
    
    print("Testing fixed downloader...")
    
    downloader = QuantScholarDownloader()
    
    # Test with small limits and dry run
    stats = await downloader.download_papers(
        sources=["arxiv"],  # Just test arXiv first
        categories=["q-fin.CP"],  # Just one category
        date_range="last-month",
        max_papers=3,
        dry_run=True,
        resume=False
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
    
    return stats['total_discovered'] > 0


if __name__ == "__main__":
    success = asyncio.run(test_fixed_downloader())
    if success:
        print("\n✅ Fix successful - papers discovered!")
    else:
        print("\n❌ Still not working")
    sys.exit(0 if success else 1)