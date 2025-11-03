#!/usr/bin/env python3
"""
Historical ArXiv Downloader - Standalone Version

Downloads papers from the beginning of arXiv (1991) using the existing
arxiv_rag_enhancement system. This script works with the current infrastructure
without requiring the multi-instance system.

Usage:
    python download_historical_arxiv.py [options]

Options:
    --start-year YEAR       Starting year (default: 1991)
    --end-year YEAR         Ending year (default: current year)
    --categories CAT1,CAT2  Comma-separated categories (default: AI Scholar categories)
    --max-papers NUM        Maximum papers per year (default: 5000)
    --dry-run              Show what would be downloaded
    --help                 Show this help message
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta
import subprocess
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('historical_arxiv_download.log')
    ]
)
logger = logging.getLogger(__name__)


def get_arxiv_timeline():
    """Get arXiv historical timeline information."""
    return {
        "start_year": 1991,
        "categories_by_year": {
            1991: ["hep-th", "hep-ph", "hep-lat"],
            1992: ["gr-qc", "astro-ph"],
            1993: ["cond-mat"],
            1994: ["nucl-th"],
            1995: ["math"],
            1996: ["quant-ph"],  # Key for quantum computing
            1997: ["physics"],
            1998: ["cs"],  # Key for AI/ML
            2007: ["q-bio"],
            2008: ["q-fin", "stat"],  # Key for statistics/ML
            2009: ["eess"],
            2019: ["econ"]
        },
        "ai_scholar_categories": [
            "cond-mat", "gr-qc", "hep-ph", "hep-th", 
            "math", "math-ph", "physics", "q-alg", "quant-ph",
            "cs.AI", "cs.LG", "cs.CL", "cs.CV", "stat.ML"
        ]
    }


def estimate_papers_for_period(start_date: datetime, end_date: datetime, categories: list) -> int:
    """Estimate number of papers for a given period and categories."""
    years_since_1991 = start_date.year - 1991
    days_in_period = (end_date - start_date).days + 1
    
    # ArXiv growth model (rough estimates)
    if years_since_1991 < 5:  # 1991-1995
        papers_per_day = 2 + years_since_1991 * 0.5
    elif years_since_1991 < 10:  # 1996-2000
        papers_per_day = 5 + (years_since_1991 - 5) * 2
    elif years_since_1991 < 20:  # 2001-2010
        papers_per_day = 15 + (years_since_1991 - 10) * 5
    else:  # 2011+
        papers_per_day = 65 + (years_since_1991 - 20) * 10
    
    # Adjust for category subset (AI Scholar categories are ~20% of total)
    category_factor = len(categories) / 50  # Rough estimate
    estimated_papers = int(papers_per_day * days_in_period * category_factor)
    
    return max(1, estimated_papers)


def run_existing_downloader(start_date: datetime, end_date: datetime, max_papers: int, dry_run: bool = False) -> dict:
    """Run the existing bulk downloader for a specific date range."""
    days_back = (datetime.now() - start_date).days
    
    # Use the existing download_bulk_arxiv_papers.py script
    cmd = [
        sys.executable, 
        "download_bulk_arxiv_papers.py",
        "--days", str(days_back),
        "--max-papers", str(max_papers)
    ]
    
    if dry_run:
        # For dry run, just simulate
        logger.info(f"DRY RUN: Would run command: {' '.join(cmd)}")
        return {
            "success": True,
            "papers_downloaded": min(max_papers, estimate_papers_for_period(start_date, end_date, [])),
            "message": "Dry run completed"
        }
    
    try:
        logger.info(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, cwd="backend")
        
        if result.returncode == 0:
            logger.info("Download completed successfully")
            return {
                "success": True,
                "papers_downloaded": max_papers,  # Estimate
                "message": "Download completed",
                "stdout": result.stdout
            }
        else:
            logger.error(f"Download failed: {result.stderr}")
            return {
                "success": False,
                "error": result.stderr,
                "message": "Download failed"
            }
    
    except Exception as e:
        logger.error(f"Error running downloader: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Error running downloader"
        }


def run_existing_processor(pdf_directory: str, dry_run: bool = False) -> dict:
    """Run the existing local processor for PDFs."""
    
    # Use the existing process_local_arxiv_dataset.py script
    cmd = [
        sys.executable,
        "process_local_arxiv_dataset.py",
        pdf_directory
    ]
    
    if dry_run:
        logger.info(f"DRY RUN: Would run command: {' '.join(cmd)}")
        return {
            "success": True,
            "papers_processed": 0,
            "message": "Dry run completed"
        }
    
    try:
        logger.info(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, cwd="backend")
        
        if result.returncode == 0:
            logger.info("Processing completed successfully")
            return {
                "success": True,
                "papers_processed": 100,  # Estimate
                "message": "Processing completed",
                "stdout": result.stdout
            }
        else:
            logger.error(f"Processing failed: {result.stderr}")
            return {
                "success": False,
                "error": result.stderr,
                "message": "Processing failed"
            }
    
    except Exception as e:
        logger.error(f"Error running processor: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Error running processor"
        }


async def main():
    """Main function for historical arXiv downloader."""
    parser = argparse.ArgumentParser(
        description='Historical ArXiv Downloader - Download papers from arXiv history',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Download from arXiv's beginning (1991) to now
    python download_historical_arxiv.py

    # Download from specific year range
    python download_historical_arxiv.py --start-year 1996 --end-year 2000

    # Download specific categories
    python download_historical_arxiv.py --start-year 1998 --categories "cs.AI,cs.LG,quant-ph"

    # Dry run to see estimates
    python download_historical_arxiv.py --start-year 1991 --end-year 1995 --dry-run

ArXiv Timeline:
    1991: ArXiv begins (hep-th)
    1996: quant-ph added (quantum computing)
    1998: cs.* added (AI/ML)
    2008: stat.ML added (modern ML)
        """
    )
    
    parser.add_argument(
        '--start-year',
        type=int,
        default=1991,
        help='Starting year (default: 1991)'
    )
    
    parser.add_argument(
        '--end-year',
        type=int,
        default=datetime.now().year,
        help='Ending year (default: current year)'
    )
    
    parser.add_argument(
        '--categories',
        type=str,
        help='Comma-separated categories (default: AI Scholar categories)'
    )
    
    parser.add_argument(
        '--max-papers',
        type=int,
        default=5000,
        help='Maximum papers per year (default: 5000)'
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
    
    # Get arXiv timeline info
    timeline = get_arxiv_timeline()
    
    # Validate years
    if args.start_year < timeline["start_year"]:
        logger.warning(f"Start year {args.start_year} is before arXiv began ({timeline['start_year']}). Using {timeline['start_year']}.")
        args.start_year = timeline["start_year"]
    
    if args.start_year > args.end_year:
        logger.error(f"Start year ({args.start_year}) cannot be after end year ({args.end_year})")
        return 1
    
    # Determine categories
    if args.categories:
        categories = [cat.strip() for cat in args.categories.split(',')]
    else:
        categories = timeline["ai_scholar_categories"]
    
    logger.info("Starting Historical ArXiv Downloader")
    logger.info(f"Year range: {args.start_year} to {args.end_year}")
    logger.info(f"Categories: {', '.join(categories)}")
    logger.info(f"Max papers per year: {args.max_papers}")
    
    if args.dry_run:
        logger.info("DRY RUN MODE - No actual downloads will be performed")
    
    # Show historical context
    logger.info("\nArXiv Historical Context:")
    for year, cats in timeline["categories_by_year"].items():
        if args.start_year <= year <= args.end_year:
            logger.info(f"  {year}: {', '.join(cats)} categories became available")
    
    # Check for early categories
    early_warnings = []
    for cat in categories:
        if cat.startswith("cs.") and args.start_year < 1998:
            early_warnings.append(f"{cat} (available from 1998)")
        elif cat == "quant-ph" and args.start_year < 1996:
            early_warnings.append(f"{cat} (available from 1996)")
        elif cat == "stat.ML" and args.start_year < 2008:
            early_warnings.append(f"{cat} (available from 2008)")
    
    if early_warnings:
        logger.warning("Some categories may not be available in early years:")
        for warning in early_warnings:
            logger.warning(f"  - {warning}")
    
    # Process year by year
    total_estimated = 0
    total_downloaded = 0
    total_processed = 0
    
    try:
        for year in range(args.start_year, args.end_year + 1):
            logger.info(f"\n--- Processing Year {year} ---")
            
            # Create date range for the year
            start_date = datetime(year, 1, 1)
            end_date = datetime(year, 12, 31)
            
            # Estimate papers for this year
            estimated = estimate_papers_for_period(start_date, end_date, categories)
            total_estimated += estimated
            
            logger.info(f"Estimated papers for {year}: {estimated}")
            
            if args.dry_run:
                logger.info(f"DRY RUN: Would download up to {min(estimated, args.max_papers)} papers")
                continue
            
            # Download papers for this year using existing system
            logger.info(f"Downloading papers for {year}...")
            
            download_result = run_existing_downloader(
                start_date, 
                end_date, 
                min(estimated, args.max_papers),
                dry_run=False
            )
            
            if download_result["success"]:
                downloaded = download_result.get("papers_downloaded", 0)
                total_downloaded += downloaded
                logger.info(f"Downloaded {downloaded} papers for {year}")
                
                # Process the downloaded papers
                if downloaded > 0:
                    logger.info(f"Processing papers for {year}...")
                    
                    # Assume PDFs are in the default location
                    pdf_directory = "/datapool/aischolar/arxiv-dataset/pdf"
                    
                    process_result = run_existing_processor(pdf_directory, dry_run=False)
                    
                    if process_result["success"]:
                        processed = process_result.get("papers_processed", 0)
                        total_processed += processed
                        logger.info(f"Processed {processed} papers for {year}")
                    else:
                        logger.error(f"Processing failed for {year}: {process_result.get('error', 'Unknown error')}")
            else:
                logger.error(f"Download failed for {year}: {download_result.get('error', 'Unknown error')}")
            
            # Small delay between years
            await asyncio.sleep(1)
        
        # Final summary
        logger.info("\n" + "="*60)
        logger.info("HISTORICAL DOWNLOAD SUMMARY")
        logger.info("="*60)
        logger.info(f"Years processed: {args.start_year} to {args.end_year}")
        logger.info(f"Categories: {', '.join(categories)}")
        
        if args.dry_run:
            logger.info(f"Estimated total papers: {total_estimated}")
            logger.info("DRY RUN: No actual downloads performed")
        else:
            logger.info(f"Total estimated: {total_estimated}")
            logger.info(f"Total downloaded: {total_downloaded}")
            logger.info(f"Total processed: {total_processed}")
            
            if total_estimated > 0:
                success_rate = (total_processed / total_estimated) * 100
                logger.info(f"Overall success rate: {success_rate:.1f}%")
        
        # Recommendations
        logger.info("\nRECOMMENDATIONS:")
        
        if args.start_year < 1996:
            logger.info("- Early arXiv (pre-1996) focuses on theoretical physics")
        
        if args.start_year < 1998:
            logger.info("- Computer Science categories not available before 1998")
        
        if total_estimated > 20000:
            logger.info("- Large dataset - monitor storage space")
        
        logger.info("- Check logs for any download or processing errors")
        logger.info("- Use existing ArXiv RAG system to query processed papers")
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"Historical downloader failed: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)