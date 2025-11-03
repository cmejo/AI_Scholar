#!/usr/bin/env python3
"""
Process Already Downloaded arXiv Papers

This script processes the PDFs that were already downloaded by the bulk downloader
and integrates them into the AI Scholar RAG system.
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add the backend directory to Python path
sys.path.append(str(Path(__file__).parent))

from arxiv_rag_enhancement.processors.local_processor import ArxivLocalProcessor

def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('process_downloaded_papers.log')
        ]
    )

async def main():
    """Main processing function."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    print("🔄 Processing Downloaded arXiv Papers")
    print("=" * 60)
    
    # Count downloaded papers
    pdf_dir = Path("/datapool/aischolar/arxiv-dataset-2024/pdfs")
    pdf_files = list(pdf_dir.rglob("*.pdf"))
    
    print(f"📁 Found {len(pdf_files)} downloaded PDF files")
    print(f"📂 Source Directory: {pdf_dir}")
    print("=" * 60)
    
    if not pdf_files:
        print("❌ No PDF files found to process")
        return
    
    # Ask for confirmation
    response = input(f"\nProcess {len(pdf_files)} downloaded papers? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("Processing cancelled")
        return
    
    try:
        # Create processor for the downloaded files
        processor = ArxivLocalProcessor(
            source_dir=str(pdf_dir),
            output_dir="/datapool/aischolar/arxiv-dataset-2024",
            batch_size=5  # Smaller batch size for stability
        )
        
        # Initialize services
        print("\n🔧 Initializing services...")
        if not await processor.initialize_services():
            print("❌ Failed to initialize services")
            return
        
        print("✅ Services initialized successfully")
        
        # Process the papers
        print(f"\n🔄 Processing {len(pdf_files)} papers...")
        start_time = datetime.now()
        
        success = await processor.process_dataset()
        
        total_time = datetime.now() - start_time
        
        # Display results
        if success:
            stats = processor.get_processing_stats()
            print("\n" + "=" * 60)
            print("PROCESSING COMPLETE")
            print("=" * 60)
            print(f"✅ Successfully processed: {stats['processed_count']} papers")
            print(f"❌ Failed to process: {stats['failed_count']} papers")
            print(f"⏱️  Total processing time: {total_time}")
            print(f"📊 Processing rate: {stats['processed_count'] / total_time.total_seconds():.2f} papers/sec")
            
            if stats['failed_count'] > 0:
                print(f"📋 Error details available in logs")
            
            print("\n🎉 Your AI Scholar chatbot now has enhanced knowledge!")
            print("   You can now ask questions about the processed research papers.")
            
        else:
            print("❌ Processing failed - check logs for details")
        
        # Cleanup
        processor.cleanup()
        
    except KeyboardInterrupt:
        print("\n⏸️  Processing interrupted by user")
        print("You can run this script again to resume processing")
        
    except Exception as e:
        logger.error(f"Processing failed: {e}", exc_info=True)
        print(f"❌ Processing failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())