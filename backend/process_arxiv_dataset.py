#!/usr/bin/env python3
"""
Script to process the arXiv dataset and populate the vector store
This script processes PDFs from /home/cmejo/arxiv-dataset/pdf
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime
import time

# Add the backend directory to the Python path
sys.path.append(str(Path(__file__).parent))

from services.scientific_pdf_processor import scientific_pdf_processor
from services.vector_store_service import vector_store_service
from services.scientific_rag_service import scientific_rag_service

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ArxivProcessor:
    """Processor for arXiv dataset"""
    
    def __init__(self, dataset_path: str = "/home/cmejo/arxiv-dataset/pdf"):
        self.dataset_path = Path(dataset_path)
        self.processed_count = 0
        self.failed_count = 0
        self.start_time = None
        
    async def initialize_services(self):
        """Initialize all required services"""
        logger.info("Initializing services...")
        
        try:
            # Configure services for localhost
            vector_store_service.chroma_host = "localhost"
            vector_store_service.chroma_port = 8082
            
            # Initialize vector store
            await vector_store_service.initialize()
            logger.info("✅ Vector store initialized")
            
            # Check health
            health = await vector_store_service.health_check()
            if health.get('status') != 'healthy':
                logger.warning(f"Vector store health: {health}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            return False
    
    async def process_dataset(self, max_files: int = None, batch_size: int = 10):
        """Process the entire arXiv dataset"""
        
        if not self.dataset_path.exists():
            logger.error(f"Dataset path does not exist: {self.dataset_path}")
            return False
        
        # Get all PDF files recursively
        pdf_files = list(self.dataset_path.rglob("*.pdf"))
        if not pdf_files:
            logger.error("No PDF files found in dataset")
            return False
        
        # Limit files if specified
        if max_files:
            pdf_files = pdf_files[:max_files]
        
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        self.start_time = time.time()
        
        # Process in batches
        for i in range(0, len(pdf_files), batch_size):
            batch = pdf_files[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(pdf_files) + batch_size - 1)//batch_size}")
            
            # Process batch concurrently
            tasks = [self.process_single_pdf(pdf_file) for pdf_file in batch]
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Log progress
            elapsed = time.time() - self.start_time
            rate = (self.processed_count + self.failed_count) / elapsed if elapsed > 0 else 0
            remaining = len(pdf_files) - (self.processed_count + self.failed_count)
            eta = remaining / rate if rate > 0 else 0
            
            logger.info(f"Progress: {self.processed_count} processed, {self.failed_count} failed")
            logger.info(f"Rate: {rate:.2f} files/sec, ETA: {eta/60:.1f} minutes")
        
        # Final summary
        total_time = time.time() - self.start_time
        logger.info("=" * 50)
        logger.info("PROCESSING COMPLETE")
        logger.info(f"Total files: {len(pdf_files)}")
        logger.info(f"Successfully processed: {self.processed_count}")
        logger.info(f"Failed: {self.failed_count}")
        logger.info(f"Total time: {total_time/60:.1f} minutes")
        logger.info(f"Average rate: {len(pdf_files)/total_time:.2f} files/sec")
        
        return True
    
    async def process_single_pdf(self, pdf_path: Path):
        """Process a single PDF file"""
        try:
            logger.debug(f"Processing: {pdf_path.name}")
            
            # Extract content from PDF
            document_data = scientific_pdf_processor.extract_comprehensive_content(str(pdf_path))
            
            # Create chunks for vector storage
            chunks = scientific_rag_service._create_scientific_chunks(document_data)
            
            if not chunks:
                logger.warning(f"No chunks created for {pdf_path.name}")
                self.failed_count += 1
                return
            
            # Add to vector store
            result = await vector_store_service.add_document_chunks(
                document_data['document_id'],
                chunks
            )
            
            self.processed_count += 1
            
            if self.processed_count % 10 == 0:
                logger.info(f"Processed {self.processed_count} files - Latest: {pdf_path.name}")
            
        except Exception as e:
            logger.error(f"Failed to process {pdf_path.name}: {e}")
            self.failed_count += 1
    
    async def get_collection_stats(self):
        """Get current collection statistics"""
        try:
            stats = await vector_store_service.get_collection_stats()
            
            logger.info("Collection Statistics:")
            logger.info(f"  Total chunks: {stats.get('total_chunks', 0)}")
            logger.info(f"  Total documents: {stats.get('document_count', 0)}")
            logger.info(f"  Average word count: {stats.get('avg_word_count', 0):.1f}")
            
            sections = stats.get('sections', {})
            if sections:
                logger.info("  Top sections:")
                for section, count in list(sections.items())[:5]:
                    logger.info(f"    {section}: {count}")
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {}

async def main():
    """Main processing function"""
    
    print("🚀 AI Scholar arXiv Dataset Processor")
    print("=" * 50)
    
    processor = ArxivProcessor()
    
    # Initialize services
    if not await processor.initialize_services():
        logger.error("Failed to initialize services")
        return
    
    # Get initial stats
    logger.info("Current collection state:")
    await processor.get_collection_stats()
    
    # Ask user for confirmation
    print("\nThis will process PDFs from: /home/cmejo/arxiv-dataset/pdf")
    
    # For automated processing, you can comment out this input
    response = input("Continue? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("Processing cancelled")
        return
    
    # Process dataset
    # Start with a small batch for testing
    max_files = input("Max files to process (press Enter for all): ").strip()
    max_files = int(max_files) if max_files.isdigit() else None
    
    success = await processor.process_dataset(max_files=max_files)
    
    if success:
        # Get final stats
        logger.info("\nFinal collection state:")
        await processor.get_collection_stats()
        
        print("\n🎉 Processing completed successfully!")
        print("You can now:")
        print("1. Start the FastAPI server: python app.py")
        print("2. Query your documents via the API")
        print("3. Use the web interface to search your papers")
    else:
        print("❌ Processing failed")

if __name__ == "__main__":
    asyncio.run(main())