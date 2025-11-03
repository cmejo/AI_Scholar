#!/usr/bin/env python3
"""
ArXiv Range Downloader - Simple Historical Downloads

Uses the existing download_bulk_arxiv_papers.py script to download papers
from large date ranges by calculating days back from current date.

Usage:
    python download_arxiv_range.py [options]

Options:
    --years-back NUM        Number of years back to download (default: 5)
    --max-papers NUM        Maximum papers to download (default: 10000)
    --dry-run              Show what would be downloaded
    --help                 Show this help message
"""

import argparse
import logging
import sys
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def calculate_days_back(years_back: int) -> int:
    """Calculate number of days back for given years."""
    return years_back * 365


def get_arxiv_milestones():
    """Get key arXiv milestones for reference."""
    current_year = datetime.now().year
    return {
        "arxiv_age": current_year - 1991,
        "milestones": {
            "Complete arXiv history": current_year - 1991,
            "Modern ML era (2015+)": current_year - 2015,
            "Deep learning era (2012+)": current_year - 2012,
            "Modern arXiv (2005+)": current_year - 2005,
            "CS categories available (1998+)": current_year - 1998,
            "Quantum physics available (1996+)": current_year - 1996,
            "Early arXiv physics (1991+)": current_year - 1991
        }
    }


def run_bulk_downloader(days_back: int, max_papers: int, dry_run: bool = False) -> dict:
    """Run the existing bulk downloader."""
    
    # Check if the bulk downloader exists
    bulk_downloader_path = Path("backend/download_bulk_arxiv_papers.py")
    if not bulk_downloader_path.exists():
        return {
            "success": False,
            "error": f"Bulk downloader not found at {bulk_downloader_path}",
            "message": "Please ensure download_bulk_arxiv_papers.py exists"
        }
    
    cmd = [
        sys.executable,
        str(bulk_downloader_path),
        "--days", str(days_back),
        "--max-papers", str(max_papers)
    ]
    
    if dry_run:
        logger.info(f"DRY RUN: Would execute command:")
        logger.info(f"  {' '.join(cmd)}")
        
        # Estimate what would be downloaded
        years = days_back / 365
        if years < 5:
            estimated_papers = min(max_papers, int(years * 2000))
        elif years < 15:
            estimated_papers = min(max_papers, int(years * 5000))
        else:
            estimated_papers = min(max_papers, int(years * 8000))
        
        return {
            "success": True,
            "estimated_papers": estimated_papers,
            "message": f"DRY RUN: Would download ~{estimated_papers} papers from last {years:.1f} years"
        }
    
    try:
        logger.info(f"Executing: {' '.join(cmd)}")
        logger.info("This may take a while for large date ranges...")
        
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True,
            timeout=3600  # 1 hour timeout
        )
        
        if result.returncode == 0:
            logger.info("Bulk download completed successfully")
            return {
                "success": True,
                "message": "Download completed successfully",
                "stdout": result.stdout[-1000:] if result.stdout else ""  # Last 1000 chars
            }
        else:
            logger.error(f"Bulk download failed with return code {result.returncode}")
            return {
                "success": False,
                "error": result.stderr,
                "message": f"Download failed with return code {result.returncode}"
            }
    
    except subprocess.TimeoutExpired:
        logger.error("Download timed out after 1 hour")
        return {
            "success": False,
            "error": "Process timed out",
            "message": "Download timed out - try smaller date range or higher max-papers limit"
        }
    except Exception as e:
        logger.error(f"Error running bulk downloader: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Error executing bulk downloader"
        }


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='ArXiv Range Downloader - Download papers from large date ranges',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Download papers from last 5 years
    python download_arxiv_range.py --years-back 5

    # Download papers from last 10 years, max 20000 papers
    python download_arxiv_range.py --years-back 10 --max-papers 20000

    # Download complete arXiv history (33+ years)
    python download_arxiv_range.py --years-back 33 --max-papers 100000

    # Dry run to see what would be downloaded
    python download_arxiv_range.py --years-back 20 --dry-run

Key Periods:
    --years-back 5   : Modern ML era (2019+)
    --years-back 10  : Deep learning era (2014+)  
    --years-back 20  : Modern arXiv (2004+)
    --years-back 27  : CS categories available (1998+)
    --years-back 29  : Quantum physics available (1996+)
    --years-back 33  : Complete arXiv history (1991+)
        """
    )
    
    parser.add_argument(
        '--years-back',
        type=int,
        default=5,
        help='Number of years back to download (default: 5)'
    )
    
    parser.add_argument(
        '--max-papers',
        type=int,
        default=10000,
        help='Maximum papers to download (default: 10000)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be downloaded without downloading'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Calculate days back
    days_back = calculate_days_back(args.years_back)
    
    # Get milestone information
    milestones = get_arxiv_milestones()
    
    logger.info("ArXiv Range Downloader")
    logger.info(f"Years back: {args.years_back}")
    logger.info(f"Days back: {days_back}")
    logger.info(f"Max papers: {args.max_papers}")
    
    if args.dry_run:
        logger.info("DRY RUN MODE - No actual downloads will be performed")
    
    # Show what period this covers
    start_year = datetime.now().year - args.years_back
    logger.info(f"Date range: {start_year} to {datetime.now().year}")
    
    # Show relevant milestones
    logger.info("\nArXiv Historical Context:")
    for milestone, years_needed in milestones["milestones"].items():
        if args.years_back >= years_needed:
            logger.info(f"  ✓ {milestone}")
        else:
            logger.info(f"  ✗ {milestone} (need {years_needed} years)")
    
    # Warnings for large downloads
    if args.years_back > 20:
        logger.warning("Large historical download detected!")
        logger.warning("This may take several hours and require significant storage")
        logger.warning("Consider using --dry-run first to estimate size")
    
    if args.max_papers > 50000:
        logger.warning("Large paper limit detected!")
        logger.warning("This may require significant processing time and storage")
    
    try:
        # Run the bulk downloader
        result = run_bulk_downloader(days_back, args.max_papers, args.dry_run)
        
        if result["success"]:
            logger.info("✓ " + result["message"])
            
            if "estimated_papers" in result:
                logger.info(f"Estimated papers: {result['estimated_papers']}")
            
            if not args.dry_run:
                logger.info("\nNext steps:")
                logger.info("1. Check the download logs for any errors")
                logger.info("2. Run process_local_arxiv_dataset.py to process downloaded PDFs")
                logger.info("3. Use the AI Scholar chat interface to query the papers")
                
                # Show processing command
                logger.info("\nTo process downloaded papers:")
                logger.info("python backend/process_local_arxiv_dataset.py /datapool/aischolar/arxiv-dataset/pdf")
        else:
            logger.error("✗ " + result["message"])
            if "error" in result:
                logger.error(f"Error details: {result['error']}")
            return 1
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"Range downloader failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)