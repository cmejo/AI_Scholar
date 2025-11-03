#!/usr/bin/env python3
"""
Debug script to test argument parsing.
"""

import sys
import argparse
from pathlib import Path

# Add backend directory to path for imports
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from multi_instance_arxiv_system.scripts.quant_scholar_downloader import create_argument_parser


def test_arg_parsing():
    """Test argument parsing with the same command line."""
    
    # Simulate the command line you used
    test_args = [
        "--sources", "arxiv,jss,rjournal",
        "--date-range", "all", 
        "--resume",
        "--verbose"
    ]
    
    parser = create_argument_parser()
    args = parser.parse_args(test_args)
    
    print("Parsed arguments:")
    print(f"  sources: {args.sources}")
    print(f"  date_range: {args.date_range}")
    print(f"  resume: {args.resume}")
    print(f"  verbose: {args.verbose}")
    
    # Parse sources
    sources = None
    if args.sources:
        sources = [src.strip() for src in args.sources.split(',')]
    
    print(f"  parsed sources: {sources}")


if __name__ == "__main__":
    test_arg_parsing()