#!/usr/bin/env python3
"""
AI Scholar Processor Script

Entry point script for processing existing PDF files into the AI Scholar vector store.
Useful for processing local PDF collections or previously downloaded papers.

Usage:
    python ai_scholar_processor.py [options] <pdf_directory>

Options:
    --config PATH       Path to AI Scholar config file (default: auto-detect)
    --batch-size NUM    Number of PDFs to process in each batch (default: 10)
    --recursive         Recursively search subdirectories for PDFs
    --pattern PATTERN   File pattern to match (default: *.pdf)
    --resume           Resume from previous interrupted run
    --force            Reprocess files even if already processed
    --help             Show this help message
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path
import glob

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('ai_scholar_processor.log')
    ]
)
logger = logging.getLogger(__name__)


def find_pdf_files(directory: Path, pattern: str = "*.pdf", recursive: bool = False) -> list:
    """Find PDF files in directory."""
    pdf_files = []
    
    if recursive:
        # Recursively search subdirectories
        search_pattern = f"**/{pattern}"
        pdf_files = list(directory.glob(search_pattern))
    else:
        # Search only in the specified directory
        pdf_files = list(directory.glob(pattern))
    
    # Convert to strings and sort
    pdf_files = [str(f) for f in pdf_files if f.is_file()]
    pdf_files.sort()
    
    return pdf_files


async def main():
    """Main function for AI Scholar processor."""
    parser = argparse.ArgumentParser(
        description='AI Scholar Processor - Process PDF files into vector store',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Process all PDFs in a directory
    python ai_scholar_processor.py /path/to/pdfs

    # Process PDFs recursively with custom batch size
    python ai_scholar_processor.py --recursive --batch-size 20 /path/to/pdfs

    # Process specific pattern of files
    python ai_scholar_processor.py --pattern "arxiv_*.pdf" /path/to/pdfs

    # Resume interrupted processing
    python ai_scholar_processor.py --resume /path/to/pdfs
        """
    )
    
    parser.add_argument(
        'pdf_directory',
        type=str,
        help='Directory containing PDF files to process'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='Path to AI Scholar config file (default: auto-detect)'
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=10,
        help='Number of PDFs to process in each batch (default: 10)'
    )
    
    parser.add_argument(
        '--recursive',
        action='store_true',
        help='Recursively search subdirectories for PDFs'
    )
    
    parser.add_argument(
        '--pattern',
        type=str,
        default='*.pdf',
        help='File pattern to match (default: *.pdf)'
    )
    
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume from previous interrupted run'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Reprocess files even if already processed'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate PDF directory
    pdf_dir = Path(args.pdf_directory)
    if not pdf_dir.exists():
        logger.error(f"PDF directory does not exist: {pdf_dir}")
        return 1
    
    if not pdf_dir.is_dir():
        logger.error(f"Path is not a directory: {pdf_dir}")
        return 1
    
    logger.info("Starting AI Scholar Processor")
    logger.info(f"PDF directory: {pdf_dir}")
    logger.info(f"Configuration: batch_size={args.batch_size}, recursive={args.recursive}, pattern={args.pattern}")
    
    try:
        # Import AI Scholar components
        from multi_instance_arxiv_system.processors.ai_scholar_processor import AIScholarProcessor
        from multi_instance_arxiv_system.shared.multi_instance_data_models import (
            InstanceConfig, StoragePaths, ProcessingConfig, 
            VectorStoreConfig, NotificationConfig
        )
        
        # Determine config path
        config_path = args.config
        if not config_path:
            # Try to find config file
            possible_paths = [
                "multi_instance_arxiv_system/configs/ai_scholar.yaml",
                "configs/ai_scholar.yaml",
                "../configs/ai_scholar.yaml"
            ]
            
            for path in possible_paths:
                if Path(path).exists():
                    config_path = path
                    break
        
        if config_path and Path(config_path).exists():
            logger.info(f"Using config file: {config_path}")
            # Load config from file
            import yaml
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            # Create instance config from YAML
            instance_config = InstanceConfig(
                instance_name=config_data['instance']['name'],
                display_name=config_data['instance']['display_name'],
                description=config_data['instance']['description'],
                arxiv_categories=config_data['data_sources']['arxiv']['categories'],
                journal_sources=config_data['data_sources'].get('journals', []),
                storage_paths=StoragePaths(**config_data['storage']),
                vector_store_config=VectorStoreConfig(**config_data['vector_store']),
                processing_config=ProcessingConfig(**config_data['processing']),
                notification_config=NotificationConfig(**config_data.get('notifications', {}))
            )
        else:
            logger.info("Using default configuration")
            # Create default config
            instance_config = InstanceConfig(
                instance_name="ai_scholar",
                display_name="AI Scholar",
                description="AI and Physics Research Papers",
                arxiv_categories=["quant-ph", "cs.AI", "physics"],
                journal_sources=[],
                storage_paths=StoragePaths(
                    pdf_directory=str(pdf_dir),
                    processed_directory="/tmp/ai_scholar/processed",
                    state_directory="/tmp/ai_scholar/state",
                    error_log_directory="/tmp/ai_scholar/errors",
                    archive_directory="/tmp/ai_scholar/archive"
                ),
                vector_store_config=VectorStoreConfig(
                    collection_name="ai_scholar_papers",
                    embedding_model="all-MiniLM-L6-v2"
                ),
                processing_config=ProcessingConfig(
                    batch_size=args.batch_size,
                    max_concurrent_processing=2
                ),
                notification_config=NotificationConfig(enabled=False)
            )
        
        # Find PDF files
        logger.info("Scanning for PDF files...")
        pdf_files = find_pdf_files(pdf_dir, args.pattern, args.recursive)
        
        if not pdf_files:
            logger.info(f"No PDF files found matching pattern '{args.pattern}' in {pdf_dir}")
            return 0
        
        logger.info(f"Found {len(pdf_files)} PDF files")
        
        # Show sample files
        for i, pdf_file in enumerate(pdf_files[:5]):
            logger.info(f"  {i+1}. {Path(pdf_file).name}")
        
        if len(pdf_files) > 5:
            logger.info(f"  ... and {len(pdf_files) - 5} more files")
        
        # Initialize processor
        processor = AIScholarProcessor(instance_config)
        
        logger.info("Initializing AI Scholar processor...")
        success = await processor.initialize()
        if not success:
            logger.error("Failed to initialize AI Scholar processor")
            return 1
        
        # Process files in batches
        batch_size = args.batch_size
        total_processed = 0
        total_failed = 0
        
        for i in range(0, len(pdf_files), batch_size):
            batch = pdf_files[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(pdf_files) + batch_size - 1) // batch_size
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} files)")
            
            try:
                # Process batch
                result = await processor.process_papers(batch)
                
                total_processed += result.success_count
                total_failed += result.failure_count
                
                logger.info(f"Batch {batch_num} completed: {result.success_count} successful, "
                           f"{result.failure_count} failed")
                
                if result.failed_papers:
                    logger.warning(f"Failed files in batch {batch_num}:")
                    for failed_file in result.failed_papers[:3]:  # Show first 3 failures
                        logger.warning(f"  - {Path(failed_file).name}")
                    if len(result.failed_papers) > 3:
                        logger.warning(f"  ... and {len(result.failed_papers) - 3} more")
                
            except Exception as e:
                logger.error(f"Batch {batch_num} failed: {e}")
                total_failed += len(batch)
        
        # Show final summary
        logger.info("Processing completed!")
        logger.info(f"Total files processed: {total_processed}")
        logger.info(f"Total files failed: {total_failed}")
        logger.info(f"Success rate: {(total_processed / len(pdf_files) * 100):.1f}%")
        
        # Get processor stats
        stats = processor.get_processing_stats()
        logger.info("Final processor statistics:")
        logger.info(f"  Instance: {stats['instance_name']}")
        logger.info(f"  Processed documents: {stats['processed_documents']}")
        
        if 'vector_store' in stats:
            vs_stats = stats['vector_store']
            logger.info(f"  Vector store documents: {vs_stats.get('document_count', 0)}")
            logger.info(f"  Collection: {vs_stats.get('collection_name', 'unknown')}")
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"AI Scholar processor failed: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return 1
    finally:
        # Cleanup
        try:
            if 'processor' in locals():
                processor.shutdown()
        except:
            pass


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)