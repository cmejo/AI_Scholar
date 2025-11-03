#!/usr/bin/env python3
"""
AI Scholar Downloader Script

This script downloads and processes papers from specific arXiv categories
for the AI Scholar instance with comprehensive command-line interface.

Usage:
    python ai_scholar_downloader.py [options]
    
Examples:
    # Download papers from last month
    python ai_scholar_downloader.py --date-range last-month
    
    # Download specific categories only
    python ai_scholar_downloader.py --categories physics,math
    
    # Resume interrupted download
    python ai_scholar_downloader.py --resume
    
    # Dry run to see what would be downloaded
    python ai_scholar_downloader.py --dry-run
"""

import sys
import argparse
import asyncio
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/ai_scholar_downloader.log')
    ]
)
logger = logging.getLogger(__name__)


class AIScholarDownloader:
    """AI Scholar paper downloader with command-line interface."""
    
    def __init__(self, config_path: str = "configs/ai_scholar.yaml"):
        self.config_path = config_path
        self.instance_name = "ai_scholar"
        
        # AI Scholar arXiv categories
        self.default_categories = [
            "cond-mat", "gr-qc", "hep-ph", "hep-th", "math", 
            "math-ph", "physics", "q-alg", "quant-ph"
        ]
        
        # Storage paths
        self.pdf_directory = "/datapool/aischolar/ai-scholar-arxiv-dataset/pdf"
        self.processed_directory = "/datapool/aischolar/ai-scholar-arxiv-dataset/processed"
        self.state_directory = "/datapool/aischolar/ai-scholar-arxiv-dataset/state"
        
        logger.info(f"AI Scholar Downloader initialized")
    
    async def download_papers(
        self,
        categories: Optional[List[str]] = None,
        date_range: str = "last-month",
        max_papers: Optional[int] = None,
        resume: bool = False,
        dry_run: bool = False
    ) -> dict:
        """
        Download papers for AI Scholar instance.
        
        Args:
            categories: List of arXiv categories to download
            date_range: Date range for papers (last-week, last-month, last-year, custom)
            max_papers: Maximum number of papers to download
            resume: Resume interrupted download
            dry_run: Show what would be downloaded without actually downloading
            
        Returns:
            Dictionary with download statistics
        """
        
        logger.info(f"Starting AI Scholar paper download")
        logger.info(f"Categories: {categories or self.default_categories}")
        logger.info(f"Date range: {date_range}")
        logger.info(f"Max papers: {max_papers or 'unlimited'}")
        logger.info(f"Resume: {resume}")
        logger.info(f"Dry run: {dry_run}")
        
        # Use default categories if none specified
        if not categories:
            categories = self.default_categories
        
        # Parse date range
        start_date, end_date = self._parse_date_range(date_range)
        
        # Create directories
        if not dry_run:
            self._create_directories()
        
        # Initialize statistics
        stats = {
            'total_discovered': 0,
            'total_downloaded': 0,
            'total_processed': 0,
            'total_failed': 0,
            'categories_processed': len(categories),
            'start_time': datetime.now(),
            'end_time': None
        }
        
        try:
            # Process each category
            for category in categories:
                logger.info(f"Processing category: {category}")
                
                # Discover papers in category
                papers = await self._discover_papers_in_category(
                    category, start_date, end_date, max_papers
                )
                
                stats['total_discovered'] += len(papers)
                logger.info(f"Discovered {len(papers)} papers in {category}")
                
                if dry_run:
                    logger.info(f"[DRY RUN] Would download {len(papers)} papers from {category}")
                    continue
                
                # Download papers
                for paper in papers:
                    try:
                        success = await self._download_paper(paper, resume)
                        if success:
                            stats['total_downloaded'] += 1
                        else:
                            stats['total_failed'] += 1
                    except Exception as e:
                        logger.error(f"Failed to download paper {paper.get('id', 'unknown')}: {e}")
                        stats['total_failed'] += 1
                
                logger.info(f"Completed category {category}: {stats['total_downloaded']} downloaded")
        
        except Exception as e:
            logger.error(f"Error during download process: {e}")
            raise
        
        finally:
            stats['end_time'] = datetime.now()
            stats['duration_minutes'] = (stats['end_time'] - stats['start_time']).total_seconds() / 60
        
        # Log final statistics
        logger.info("AI Scholar download completed")
        logger.info(f"Total discovered: {stats['total_discovered']}")
        logger.info(f"Total downloaded: {stats['total_downloaded']}")
        logger.info(f"Total failed: {stats['total_failed']}")
        logger.info(f"Duration: {stats['duration_minutes']:.1f} minutes")
        
        return stats
    
    def _parse_date_range(self, date_range: str) -> tuple:
        """Parse date range string into start and end dates."""
        
        end_date = datetime.now()
        
        if date_range == "last-week":
            start_date = end_date - timedelta(weeks=1)
        elif date_range == "last-month":
            start_date = end_date - timedelta(days=30)
        elif date_range == "last-year":
            start_date = end_date - timedelta(days=365)
        elif date_range == "all":
            start_date = datetime(2020, 1, 1)  # Start from 2020
        else:
            # Default to last month
            start_date = end_date - timedelta(days=30)
        
        return start_date, end_date
    
    def _create_directories(self) -> None:
        """Create necessary directories."""
        
        directories = [
            self.pdf_directory,
            self.processed_directory,
            self.state_directory,
            "logs"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {directory}")
    
    async def _discover_papers_in_category(
        self,
        category: str,
        start_date: datetime,
        end_date: datetime,
        max_papers: Optional[int]
    ) -> List[dict]:
        """
        Discover papers in a specific arXiv category.
        
        This is a placeholder implementation. In a real system, this would
        query the arXiv API or use Google Cloud Storage bulk data access.
        """
        
        logger.info(f"Discovering papers in {category} from {start_date.date()} to {end_date.date()}")
        
        # Placeholder implementation
        # In reality, this would query arXiv API
        papers = []
        
        # Simulate discovering papers
        import random
        num_papers = random.randint(10, 100)
        if max_papers:
            num_papers = min(num_papers, max_papers)
        
        for i in range(num_papers):
            paper = {
                'id': f"{category}.{random.randint(1000, 9999)}",
                'title': f"Sample Paper {i+1} in {category}",
                'authors': ["Author A", "Author B"],
                'abstract': f"This is a sample abstract for paper {i+1} in category {category}",
                'category': category,
                'published_date': start_date + timedelta(days=random.randint(0, (end_date - start_date).days)),
                'pdf_url': f"https://arxiv.org/pdf/{category}.{random.randint(1000, 9999)}.pdf"
            }
            papers.append(paper)
        
        return papers
    
    async def _download_paper(self, paper: dict, resume: bool = False) -> bool:
        """
        Download a single paper.
        
        Args:
            paper: Paper metadata dictionary
            resume: Whether to skip if already downloaded
            
        Returns:
            True if successful, False otherwise
        """
        
        paper_id = paper['id']
        pdf_path = Path(self.pdf_directory) / f"{paper_id}.pdf"
        
        # Check if already downloaded and resume is enabled
        if resume and pdf_path.exists():
            logger.debug(f"Skipping {paper_id} (already downloaded)")
            return True
        
        try:
            logger.debug(f"Downloading {paper_id}")
            
            # Simulate download
            await asyncio.sleep(0.1)  # Simulate network delay
            
            # Create placeholder PDF file
            pdf_path.parent.mkdir(parents=True, exist_ok=True)
            with open(pdf_path, 'w') as f:
                f.write(f"Placeholder PDF content for {paper_id}")
            
            # Save metadata
            metadata_path = pdf_path.with_suffix('.json')
            import json
            with open(metadata_path, 'w') as f:
                json.dump(paper, f, indent=2, default=str)
            
            logger.debug(f"Successfully downloaded {paper_id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to download {paper_id}: {e}")
            return False
    
    def get_download_status(self) -> dict:
        """Get current download status and statistics."""
        
        pdf_dir = Path(self.pdf_directory)
        processed_dir = Path(self.processed_directory)
        
        status = {
            'instance_name': self.instance_name,
            'pdf_directory': str(pdf_dir),
            'processed_directory': str(processed_dir),
            'total_pdfs': len(list(pdf_dir.glob("*.pdf"))) if pdf_dir.exists() else 0,
            'total_processed': len(list(processed_dir.glob("*.json"))) if processed_dir.exists() else 0,
            'categories': self.default_categories,
            'last_check': datetime.now().isoformat()
        }
        
        return status


def create_argument_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser."""
    
    parser = argparse.ArgumentParser(
        description="AI Scholar Paper Downloader",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --date-range last-month
  %(prog)s --categories physics,math --max-papers 100
  %(prog)s --resume --verbose
  %(prog)s --dry-run --date-range last-week
        """
    )
    
    parser.add_argument(
        '--categories',
        type=str,
        help='Comma-separated list of arXiv categories (default: all AI Scholar categories)'
    )
    
    parser.add_argument(
        '--date-range',
        choices=['last-week', 'last-month', 'last-year', 'all'],
        default='last-month',
        help='Date range for papers to download (default: last-month)'
    )
    
    parser.add_argument(
        '--max-papers',
        type=int,
        help='Maximum number of papers to download per category'
    )
    
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume interrupted download (skip already downloaded papers)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be downloaded without actually downloading'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='configs/ai_scholar.yaml',
        help='Path to configuration file'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show current download status and exit'
    )
    
    return parser


async def main():
    """Main entry point for AI Scholar downloader."""
    
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create downloader instance
    downloader = AIScholarDownloader(args.config)
    
    try:
        # Show status if requested
        if args.status:
            status = downloader.get_download_status()
            print("\nAI Scholar Download Status:")
            print("=" * 40)
            for key, value in status.items():
                print(f"{key}: {value}")
            return
        
        # Parse categories
        categories = None
        if args.categories:
            categories = [cat.strip() for cat in args.categories.split(',')]
        
        # Run download
        stats = await downloader.download_papers(
            categories=categories,
            date_range=args.date_range,
            max_papers=args.max_papers,
            resume=args.resume,
            dry_run=args.dry_run
        )
        
        # Print summary
        print("\nDownload Summary:")
        print("=" * 40)
        print(f"Papers discovered: {stats['total_discovered']}")
        print(f"Papers downloaded: {stats['total_downloaded']}")
        print(f"Papers failed: {stats['total_failed']}")
        print(f"Categories processed: {stats['categories_processed']}")
        print(f"Duration: {stats['duration_minutes']:.1f} minutes")
        
        if stats['total_failed'] > 0:
            print(f"\nWarning: {stats['total_failed']} papers failed to download")
            print("Check logs for details")
    
    except KeyboardInterrupt:
        logger.info("Download interrupted by user")
        print("\nDownload interrupted by user")
    
    except Exception as e:
        logger.error(f"Download failed: {e}")
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())