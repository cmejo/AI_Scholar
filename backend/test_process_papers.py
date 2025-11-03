#!/usr/bin/env python3
"""
Test Processing of Downloaded Papers

This script processes a small batch of downloaded papers to test the system.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the backend directory to Python path
sys.path.append(str(Path(__file__).parent))

from arxiv_rag_enhancement.processors.local_processor import ArxivLocalProcessor

async def main():
    """Test processing with a small batch."""
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 Testing Paper Processing with Small Batch")
    print("=" * 60)
    
    # Find some PDFs to test with
    pdf_dir = Path("/datapool/aischolar/arxiv-dataset-2024/pdfs")
    pdf_files = list(pdf_dir.rglob("*.pdf"))[:10]  # Just test with 10 files
    
    if not pdf_files:
        print("❌ No PDF files found")
        return
    
    print(f"📁 Testing with {len(pdf_files)} PDF files")
    for pdf in pdf_files:
        print(f"  - {pdf.name}")
    
    try:
        # Create processor
        processor = ArxivLocalProcessor(
            source_dir=str(pdf_dir),
            output_dir="/datapool/aischolar/arxiv-dataset-2024",
            batch_size=2  # Small batch for testing
        )
        
        # Initialize services
        print("\n🔧 Initializing services...")
        if not await processor.initialize_services():
            print("❌ Failed to initialize services")
            return
        
        print("✅ Services initialized successfully")
        
        # Process just a few papers
        print(f"\n🔄 Processing {len(pdf_files)} test papers...")
        success = await processor.process_dataset(max_files=10)
        
        if success:
            stats = processor.get_processing_stats()
            print("\n✅ Test processing completed!")
            print(f"   Processed: {stats['processed_count']} papers")
            print(f"   Failed: {stats['failed_count']} papers")
            
            if stats['processed_count'] > 0:
                print("\n🎉 System is working! You can now process all papers.")
                print("   Run: python backend/process_downloaded_papers.py")
            
        else:
            print("❌ Test processing failed")
        
        processor.cleanup()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())