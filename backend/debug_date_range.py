#!/usr/bin/env python3
"""
Debug script to test date range parsing.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add backend directory to path for imports
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from multi_instance_arxiv_system.scripts.quant_scholar_downloader import QuantScholarDownloader


def test_date_parsing():
    """Test date range parsing."""
    
    downloader = QuantScholarDownloader()
    
    test_ranges = ["last-week", "last-month", "last-year", "all"]
    
    for date_range in test_ranges:
        start_date, end_date = downloader._parse_date_range(date_range)
        print(f"Date range '{date_range}':")
        print(f"  Start: {start_date}")
        print(f"  End: {end_date}")
        print(f"  Start year: {start_date.year}")
        print(f"  Is 'all' range (start < 2000): {start_date.year < 2000}")
        print()


if __name__ == "__main__":
    test_date_parsing()