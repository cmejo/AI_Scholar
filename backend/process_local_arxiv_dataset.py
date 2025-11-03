#!/usr/bin/env python3
"""
Script 1: Local arXiv Dataset Processor

This script processes all existing arXiv PDFs from the local dataset directory
(~/arxiv-dataset/pdf) and integrates them into the AI Scholar RAG system.

Features:
- Recursive PDF discovery in source directory
- Real-time progress tracking with ETA
- Resume functionality for interrupted processing
- Comprehensive error handling and logging
- Integration with existing ChromaDB vector store
- Batch processing with concurrency control

Usage:
    python process_local_arxiv_dataset.py [options]

Options:
    --source-dir: Source directory containing PDFs (default: ~/arxiv-dataset/pdf)
    --output-dir: Output directory for processed files (default: /datapool/aischolar/arxiv-dataset-2024)
    --max-files: Maximum number of files to process (default: all)
    --batch-size: Batch size for processing (default: 10)
    --resume: Resume from previous state if available
    --verbose: Enable verbose logging
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add the backend directory to Python path
sys.path.append(str(Path(__file__).parent))

from arxiv_rag_enhancement.processors.local_processor import ArxivLocalProcessor, process_local_dataset

# Configure logging
def setup_logging(verbose: bool = False):
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    
    # File handler
    log_file = Path("/datapool/aischolar/arxiv-dataset-2024/processed/error_logs/local_processor.log")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Reduce noise from some libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Process local arXiv dataset for AI Scholar RAG system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Process all PDFs in default directory
    python process_local_arxiv_dataset.py
    
    # Process first 100 PDFs with verbose logging
    python process_local_arxiv_dataset.py --max-files 100 --verbose
    
    # Resume previous processing
    python process_local_arxiv_dataset.py --resume
    
    # Use custom directories
    python process_local_arxiv_dataset.py --source-dir /path/to/pdfs --output-dir /path/to/output
        """
    )
    
    parser.add_argument(
        '--source-dir',
        type=str,
        default='~/arxiv-dataset/pdf',
        help='Source directory containing PDF files (default: ~/arxiv-dataset/pdf)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='/datapool/aischolar/arxiv-dataset-2024',
        help='Output directory for processed files (default: /datapool/aischolar/arxiv-dataset-2024)'
    )
    
    parser.add_argument(
        '--max-files',
        type=int,
        default=None,
        help='Maximum number of files to process (default: all files)'
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=10,
        help='Number of files to process in each batch (default: 10)'
    )
    
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume from previous processing state if available'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be processed without actually processing'
    )
    
    return parser.parse_args()


async def main():
    """Main processing function."""
    args = parse_arguments()
    
    # Set up logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    print("🚀 AI Scholar Local arXiv Dataset Processor")
    print("=" * 60)
    print(f"Source Directory: {args.source_dir}")
    print(f"Output Directory: {args.output_dir}")
    print(f"Max Files: {args.max_files or 'All'}")
    print(f"Batch Size: {args.batch_size}")
    print(f"Resume Mode: {'Yes' if args.resume else 'No'}")
    print("=" * 60)
    
    try:
        # Create processor
        processor = ArxivLocalProcessor(
            source_dir=args.source_dir,
            output_dir=args.output_dir,
            batch_size=args.batch_size
        )
        
        # Dry run mode
        if args.dry_run:
            logger.info("DRY RUN MODE - No files will be processed")
            
            # Discover files
            pdf_files = processor.pdf_discovery.discover_pdfs(args.max_files)
            dir_stats = processor.pdf_discovery.get_directory_stats()
            
            print(f"\nWould process {len(pdf_files)} PDF files:")
            print(f"Total size: {dir_stats.get('total_size_mb', 0):.1f} MB")
            
            if len(pdf_files) <= 10:
                for pdf_file in pdf_files:
                    print(f"  - {pdf_file}")
            else:
                for pdf_file in pdf_files[:5]:
                    print(f"  - {pdf_file}")
                print(f"  ... and {len(pdf_files) - 10} more files")
                for pdf_file in pdf_files[-5:]:
                    print(f"  - {pdf_file}")
            
            return
        
        # Initialize services
        logger.info("Initializing services...")
        if not await processor.initialize_services():
            logger.error("Failed to initialize services")
            print("❌ Service initialization failed")
            return
        
        print("✅ Services initialized successfully")
        
        # Get current collection stats
        logger.info("Getting current collection statistics...")
        try:
            from services.vector_store_service import vector_store_service
            stats = await vector_store_service.get_collection_stats()
            print(f"Current collection: {stats.get('total_chunks', 0)} chunks from {stats.get('document_count', 0)} documents")
        except Exception as e:
            logger.warning(f"Could not get collection stats: {e}")
        
        # Confirm processing
        if not args.resume:
            response = input(f"\nProcess PDFs from {args.source_dir}? (y/N): ").strip().lower()
            if response not in ['y', 'yes']:
                print("Processing cancelled")
                return
        
        # Start processing
        start_time = datetime.now()
        
        if args.resume:
            logger.info("Attempting to resume previous processing...")
            success = await processor.resume_processing()
        else:
            logger.info("Starting fresh processing...")
            success = await processor.process_dataset(args.max_files)
        
        # Calculate total time
        total_time = datetime.now() - start_time
        
        # Display results
        if success:
            print("\n🎉 Processing completed successfully!")
            
            # Get final stats
            final_stats = processor.get_processing_stats()
            print(f"✅ Processed: {final_stats['processed_count']} files")
            print(f"❌ Failed: {final_stats['failed_count']} files")
            print(f"⏱️  Total time: {total_time}")
            
            if final_stats['failed_count'] > 0:
                print(f"📋 Error report available in: {processor.error_log_dir}")
            
            # Get updated collection stats
            try:
                stats = await vector_store_service.get_collection_stats()
                print(f"📊 Updated collection: {stats.get('total_chunks', 0)} chunks from {stats.get('document_count', 0)} documents")
            except Exception as e:
                logger.warning(f"Could not get updated collection stats: {e}")
            
            print("\nYour AI Scholar chatbot now has enhanced knowledge from the processed papers!")
            
        else:
            print("❌ Processing failed")
            print("Check the logs for detailed error information")
        
        # Cleanup
        processor.cleanup()
        
    except KeyboardInterrupt:
        print("\n⏸️  Processing interrupted by user")
        logger.info("Processing interrupted by user")
        
        # The state should be automatically saved due to the interrupt
        print("Progress has been saved. Use --resume to continue later.")
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"❌ Unexpected error: {e}")
        print("Check the logs for detailed error information")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())