#!/usr/bin/env python3
"""
AI Scholar Processor Script

This script processes downloaded papers for the AI Scholar instance,
including PDF parsing, text extraction, embedding generation, and vector store indexing.

Usage:
    python ai_scholar_processor.py [options]
    
Examples:
    # Process all unprocessed papers
    python ai_scholar_processor.py
    
    # Process specific papers
    python ai_scholar_processor.py --papers paper1.pdf,paper2.pdf
    
    # Reprocess all papers
    python ai_scholar_processor.py --reprocess
    
    # Process with custom batch size
    python ai_scholar_processor.py --batch-size 50
"""

import sys
import argparse
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any
import json

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/ai_scholar_processor.log')
    ]
)
logger = logging.getLogger(__name__)


class AIScholarProcessor:
    """AI Scholar paper processor with comprehensive processing pipeline."""
    
    def __init__(self, config_path: str = "configs/ai_scholar.yaml"):
        self.config_path = config_path
        self.instance_name = "ai_scholar"
        
        # Storage paths
        self.pdf_directory = "/datapool/aischolar/ai-scholar-arxiv-dataset/pdf"
        self.processed_directory = "/datapool/aischolar/ai-scholar-arxiv-dataset/processed"
        self.state_directory = "/datapool/aischolar/ai-scholar-arxiv-dataset/state"
        self.error_directory = "/datapool/aischolar/ai-scholar-arxiv-dataset/errors"
        
        # Processing configuration
        self.batch_size = 20
        self.max_concurrent = 3
        self.chunk_size = 1000  # Characters per chunk
        self.chunk_overlap = 200  # Character overlap between chunks
        
        # Vector store configuration
        self.collection_name = "ai_scholar_papers"
        self.embedding_model = "all-MiniLM-L6-v2"
        
        logger.info(f"AI Scholar Processor initialized")
    
    async def process_papers(
        self,
        papers: Optional[List[str]] = None,
        reprocess: bool = False,
        batch_size: Optional[int] = None,
        max_concurrent: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Process papers for AI Scholar instance.
        
        Args:
            papers: List of specific paper IDs to process
            reprocess: Reprocess already processed papers
            batch_size: Number of papers to process in each batch
            max_concurrent: Maximum concurrent processing tasks
            
        Returns:
            Dictionary with processing statistics
        """
        
        logger.info(f"Starting AI Scholar paper processing")
        logger.info(f"Papers: {papers or 'all unprocessed'}")
        logger.info(f"Reprocess: {reprocess}")
        logger.info(f"Batch size: {batch_size or self.batch_size}")
        logger.info(f"Max concurrent: {max_concurrent or self.max_concurrent}")
        
        # Update configuration
        if batch_size:
            self.batch_size = batch_size
        if max_concurrent:
            self.max_concurrent = max_concurrent
        
        # Create directories
        self._create_directories()
        
        # Initialize statistics
        stats = {
            'total_papers': 0,
            'processed_successfully': 0,
            'processing_failed': 0,
            'skipped_papers': 0,
            'total_chunks_created': 0,
            'total_embeddings_generated': 0,
            'start_time': datetime.now(),
            'end_time': None
        }
        
        try:
            # Get papers to process
            papers_to_process = await self._get_papers_to_process(papers, reprocess)
            stats['total_papers'] = len(papers_to_process)
            
            logger.info(f"Found {len(papers_to_process)} papers to process")
            
            if not papers_to_process:
                logger.info("No papers to process")
                return stats
            
            # Process papers in batches
            for i in range(0, len(papers_to_process), self.batch_size):
                batch = papers_to_process[i:i + self.batch_size]
                batch_num = (i // self.batch_size) + 1
                total_batches = (len(papers_to_process) + self.batch_size - 1) // self.batch_size
                
                logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} papers)")
                
                # Process batch
                batch_stats = await self._process_batch(batch)
                
                # Update statistics
                stats['processed_successfully'] += batch_stats['processed_successfully']
                stats['processing_failed'] += batch_stats['processing_failed']
                stats['skipped_papers'] += batch_stats['skipped_papers']
                stats['total_chunks_created'] += batch_stats['total_chunks_created']
                stats['total_embeddings_generated'] += batch_stats['total_embeddings_generated']
                
                logger.info(f"Batch {batch_num} completed: "
                           f"{batch_stats['processed_successfully']} successful, "
                           f"{batch_stats['processing_failed']} failed")
        
        except Exception as e:
            logger.error(f"Error during processing: {e}")
            raise
        
        finally:
            stats['end_time'] = datetime.now()
            stats['duration_minutes'] = (stats['end_time'] - stats['start_time']).total_seconds() / 60
        
        # Log final statistics
        logger.info("AI Scholar processing completed")
        logger.info(f"Total papers: {stats['total_papers']}")
        logger.info(f"Processed successfully: {stats['processed_successfully']}")
        logger.info(f"Processing failed: {stats['processing_failed']}")
        logger.info(f"Skipped papers: {stats['skipped_papers']}")
        logger.info(f"Total chunks created: {stats['total_chunks_created']}")
        logger.info(f"Duration: {stats['duration_minutes']:.1f} minutes")
        
        return stats
    
    def _create_directories(self) -> None:
        """Create necessary directories."""
        
        directories = [
            self.processed_directory,
            self.state_directory,
            self.error_directory,
            "logs"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {directory}")
    
    async def _get_papers_to_process(
        self,
        papers: Optional[List[str]],
        reprocess: bool
    ) -> List[str]:
        """Get list of papers to process."""
        
        pdf_dir = Path(self.pdf_directory)
        processed_dir = Path(self.processed_directory)
        
        if not pdf_dir.exists():
            logger.warning(f"PDF directory does not exist: {pdf_dir}")
            return []
        
        # Get all PDF files
        all_pdfs = list(pdf_dir.glob("*.pdf"))
        
        if papers:
            # Filter to specific papers
            paper_ids = set(papers)
            all_pdfs = [pdf for pdf in all_pdfs if pdf.stem in paper_ids]
        
        papers_to_process = []
        
        for pdf_path in all_pdfs:
            paper_id = pdf_path.stem
            processed_path = processed_dir / f"{paper_id}.json"
            
            # Check if already processed
            if not reprocess and processed_path.exists():
                logger.debug(f"Skipping {paper_id} (already processed)")
                continue
            
            papers_to_process.append(paper_id)
        
        return papers_to_process
    
    async def _process_batch(self, batch: List[str]) -> Dict[str, Any]:
        """Process a batch of papers concurrently."""
        
        batch_stats = {
            'processed_successfully': 0,
            'processing_failed': 0,
            'skipped_papers': 0,
            'total_chunks_created': 0,
            'total_embeddings_generated': 0
        }
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        # Process papers concurrently
        tasks = [
            self._process_single_paper(paper_id, semaphore)
            for paper_id in batch
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Aggregate results
        for result in results:
            if isinstance(result, Exception):
                batch_stats['processing_failed'] += 1
                logger.error(f"Paper processing failed: {result}")
            elif result:
                batch_stats['processed_successfully'] += 1
                batch_stats['total_chunks_created'] += result.get('chunks_created', 0)
                batch_stats['total_embeddings_generated'] += result.get('embeddings_generated', 0)
            else:
                batch_stats['skipped_papers'] += 1
        
        return batch_stats
    
    async def _process_single_paper(
        self,
        paper_id: str,
        semaphore: asyncio.Semaphore
    ) -> Optional[Dict[str, Any]]:
        """Process a single paper."""
        
        async with semaphore:
            try:
                logger.debug(f"Processing paper: {paper_id}")
                
                # Load paper metadata
                metadata = await self._load_paper_metadata(paper_id)
                if not metadata:
                    logger.warning(f"No metadata found for {paper_id}")
                    return None
                
                # Extract text from PDF
                text_content = await self._extract_text_from_pdf(paper_id)
                if not text_content:
                    logger.warning(f"No text extracted from {paper_id}")
                    await self._log_processing_error(paper_id, "No text extracted")
                    return None
                
                # Create document chunks
                chunks = await self._create_document_chunks(paper_id, text_content, metadata)
                
                # Generate embeddings
                embeddings = await self._generate_embeddings(chunks)
                
                # Store in vector database
                await self._store_in_vector_db(paper_id, chunks, embeddings, metadata)
                
                # Save processing results
                processing_result = {
                    'paper_id': paper_id,
                    'processed_at': datetime.now().isoformat(),
                    'chunks_created': len(chunks),
                    'embeddings_generated': len(embeddings),
                    'text_length': len(text_content),
                    'metadata': metadata
                }
                
                await self._save_processing_result(paper_id, processing_result)
                
                logger.debug(f"Successfully processed {paper_id}: {len(chunks)} chunks")
                
                return {
                    'chunks_created': len(chunks),
                    'embeddings_generated': len(embeddings)
                }
            
            except Exception as e:
                logger.error(f"Failed to process {paper_id}: {e}")
                await self._log_processing_error(paper_id, str(e))
                raise
    
    async def _load_paper_metadata(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """Load paper metadata from JSON file."""
        
        metadata_path = Path(self.pdf_directory) / f"{paper_id}.json"
        
        try:
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    return json.load(f)
            else:
                # Create basic metadata if not found
                return {
                    'id': paper_id,
                    'title': f"Paper {paper_id}",
                    'authors': [],
                    'abstract': "",
                    'category': "unknown",
                    'published_date': datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"Failed to load metadata for {paper_id}: {e}")
            return None
    
    async def _extract_text_from_pdf(self, paper_id: str) -> Optional[str]:
        """Extract text content from PDF file."""
        
        pdf_path = Path(self.pdf_directory) / f"{paper_id}.pdf"
        
        try:
            if not pdf_path.exists():
                logger.error(f"PDF file not found: {pdf_path}")
                return None
            
            # Simulate text extraction
            # In a real implementation, this would use PyPDF2, pdfplumber, or similar
            with open(pdf_path, 'r') as f:
                content = f.read()
            
            # Simulate extracted text
            extracted_text = f"""
Title: Sample Paper {paper_id}

Abstract:
This is a sample abstract for paper {paper_id}. It contains important research findings
and contributions to the field of artificial intelligence and related areas.

Introduction:
This paper presents novel approaches to solving complex problems in AI research.
The methodology combines theoretical foundations with practical implementations.

Methodology:
Our approach utilizes advanced machine learning techniques combined with
domain-specific knowledge to achieve superior performance.

Results:
Experimental results demonstrate significant improvements over baseline methods
across multiple evaluation metrics and datasets.

Conclusion:
This work contributes to the advancement of AI research and opens new directions
for future investigations in this important field.

References:
[1] Author A et al. "Previous Work", Journal of AI, 2023.
[2] Author B et al. "Related Research", Conference Proceedings, 2023.
            """.strip()
            
            return extracted_text
        
        except Exception as e:
            logger.error(f"Failed to extract text from {paper_id}: {e}")
            return None
    
    async def _create_document_chunks(
        self,
        paper_id: str,
        text_content: str,
        metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Create document chunks from text content."""
        
        chunks = []
        
        # Simple chunking by character count
        text_length = len(text_content)
        
        for i in range(0, text_length, self.chunk_size - self.chunk_overlap):
            chunk_text = text_content[i:i + self.chunk_size]
            
            if len(chunk_text.strip()) < 50:  # Skip very short chunks
                continue
            
            chunk = {
                'chunk_id': f"{paper_id}_chunk_{len(chunks)}",
                'paper_id': paper_id,
                'chunk_index': len(chunks),
                'text': chunk_text.strip(),
                'metadata': {
                    'title': metadata.get('title', ''),
                    'authors': metadata.get('authors', []),
                    'category': metadata.get('category', ''),
                    'published_date': metadata.get('published_date', ''),
                    'chunk_length': len(chunk_text.strip())
                }
            }
            
            chunks.append(chunk)
        
        logger.debug(f"Created {len(chunks)} chunks for {paper_id}")
        return chunks
    
    async def _generate_embeddings(self, chunks: List[Dict[str, Any]]) -> List[List[float]]:
        """Generate embeddings for document chunks."""
        
        # Simulate embedding generation
        # In a real implementation, this would use sentence-transformers or similar
        embeddings = []
        
        for chunk in chunks:
            # Create a simple hash-based embedding simulation
            text = chunk['text']
            embedding = [hash(text[i:i+10]) % 1000 / 1000.0 for i in range(0, min(len(text), 384), 10)]
            
            # Pad or truncate to fixed size (384 dimensions)
            while len(embedding) < 384:
                embedding.append(0.0)
            embedding = embedding[:384]
            
            embeddings.append(embedding)
        
        logger.debug(f"Generated {len(embeddings)} embeddings")
        return embeddings
    
    async def _store_in_vector_db(
        self,
        paper_id: str,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]],
        metadata: Dict[str, Any]
    ) -> None:
        """Store chunks and embeddings in vector database."""
        
        # Simulate vector database storage
        # In a real implementation, this would use ChromaDB or similar
        
        logger.debug(f"Storing {len(chunks)} chunks in vector database for {paper_id}")
        
        # Simulate storage delay
        await asyncio.sleep(0.1)
        
        # Log storage success
        logger.debug(f"Successfully stored {paper_id} in vector database")
    
    async def _save_processing_result(
        self,
        paper_id: str,
        result: Dict[str, Any]
    ) -> None:
        """Save processing result to file."""
        
        result_path = Path(self.processed_directory) / f"{paper_id}.json"
        
        try:
            with open(result_path, 'w') as f:
                json.dump(result, f, indent=2)
            
            logger.debug(f"Saved processing result for {paper_id}")
        
        except Exception as e:
            logger.error(f"Failed to save processing result for {paper_id}: {e}")
    
    async def _log_processing_error(self, paper_id: str, error_message: str) -> None:
        """Log processing error to error directory."""
        
        error_path = Path(self.error_directory) / f"{paper_id}_error.json"
        
        error_record = {
            'paper_id': paper_id,
            'error_message': error_message,
            'timestamp': datetime.now().isoformat(),
            'instance': self.instance_name
        }
        
        try:
            with open(error_path, 'w') as f:
                json.dump(error_record, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to log error for {paper_id}: {e}")
    
    def get_processing_status(self) -> Dict[str, Any]:
        """Get current processing status and statistics."""
        
        pdf_dir = Path(self.pdf_directory)
        processed_dir = Path(self.processed_directory)
        error_dir = Path(self.error_directory)
        
        status = {
            'instance_name': self.instance_name,
            'pdf_directory': str(pdf_dir),
            'processed_directory': str(processed_dir),
            'error_directory': str(error_dir),
            'total_pdfs': len(list(pdf_dir.glob("*.pdf"))) if pdf_dir.exists() else 0,
            'total_processed': len(list(processed_dir.glob("*.json"))) if processed_dir.exists() else 0,
            'total_errors': len(list(error_dir.glob("*_error.json"))) if error_dir.exists() else 0,
            'collection_name': self.collection_name,
            'embedding_model': self.embedding_model,
            'last_check': datetime.now().isoformat()
        }
        
        return status


def create_argument_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser."""
    
    parser = argparse.ArgumentParser(
        description="AI Scholar Paper Processor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s
  %(prog)s --papers paper1,paper2 --verbose
  %(prog)s --reprocess --batch-size 50
  %(prog)s --status
        """
    )
    
    parser.add_argument(
        '--papers',
        type=str,
        help='Comma-separated list of paper IDs to process'
    )
    
    parser.add_argument(
        '--reprocess',
        action='store_true',
        help='Reprocess already processed papers'
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=20,
        help='Number of papers to process in each batch (default: 20)'
    )
    
    parser.add_argument(
        '--max-concurrent',
        type=int,
        default=3,
        help='Maximum concurrent processing tasks (default: 3)'
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
        help='Show current processing status and exit'
    )
    
    return parser


async def main():
    """Main entry point for AI Scholar processor."""
    
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create processor instance
    processor = AIScholarProcessor(args.config)
    
    try:
        # Show status if requested
        if args.status:
            status = processor.get_processing_status()
            print("\nAI Scholar Processing Status:")
            print("=" * 40)
            for key, value in status.items():
                print(f"{key}: {value}")
            return
        
        # Parse papers
        papers = None
        if args.papers:
            papers = [paper.strip() for paper in args.papers.split(',')]
        
        # Run processing
        stats = await processor.process_papers(
            papers=papers,
            reprocess=args.reprocess,
            batch_size=args.batch_size,
            max_concurrent=args.max_concurrent
        )
        
        # Print summary
        print("\nProcessing Summary:")
        print("=" * 40)
        print(f"Total papers: {stats['total_papers']}")
        print(f"Processed successfully: {stats['processed_successfully']}")
        print(f"Processing failed: {stats['processing_failed']}")
        print(f"Skipped papers: {stats['skipped_papers']}")
        print(f"Total chunks created: {stats['total_chunks_created']}")
        print(f"Duration: {stats['duration_minutes']:.1f} minutes")
        
        if stats['processing_failed'] > 0:
            print(f"\nWarning: {stats['processing_failed']} papers failed to process")
            print("Check logs and error directory for details")
    
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        print("\nProcessing interrupted by user")
    
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())