"""
Local Dataset Processor for arXiv RAG Enhancement system.

Processes existing PDFs from local dataset directory, with support for:
- Recursive PDF file discovery
- Batch processing with concurrency control
- Progress tracking and resume functionality
- Integration with existing RAG infrastructure
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import time
import os

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from ..shared import (
    StateManager, 
    ProgressTracker, 
    ErrorHandler,
    ProcessingState,
    ProcessingStats
)

# Import existing services
try:
    from services.scientific_pdf_processor import scientific_pdf_processor
    from services.vector_store_service import vector_store_service
    from services.scientific_rag_service import scientific_rag_service
except ImportError as e:
    logging.warning(f"Could not import existing services: {e}")
    scientific_pdf_processor = None
    vector_store_service = None
    scientific_rag_service = None

logger = logging.getLogger(__name__)


class PDFDiscovery:
    """Handles recursive discovery of PDF files in source directory."""
    
    def __init__(self, source_dir: Path):
        self.source_dir = Path(source_dir)
        
    def discover_pdfs(self, max_files: Optional[int] = None) -> List[Path]:
        """
        Recursively discover PDF files in source directory.
        
        Args:
            max_files: Maximum number of files to return (None for all)
            
        Returns:
            List of PDF file paths
        """
        if not self.source_dir.exists():
            logger.error(f"Source directory does not exist: {self.source_dir}")
            return []
        
        logger.info(f"Discovering PDF files in {self.source_dir}")
        
        # Find all PDF files recursively
        pdf_files = list(self.source_dir.rglob("*.pdf"))
        
        # Sort for consistent ordering
        pdf_files.sort()
        
        # Limit if requested
        if max_files and len(pdf_files) > max_files:
            pdf_files = pdf_files[:max_files]
            logger.info(f"Limited to first {max_files} files")
        
        logger.info(f"Discovered {len(pdf_files)} PDF files")
        return pdf_files
    
    def get_directory_stats(self) -> Dict[str, Any]:
        """Get statistics about the source directory."""
        if not self.source_dir.exists():
            return {'error': 'Directory does not exist'}
        
        pdf_files = list(self.source_dir.rglob("*.pdf"))
        total_size = sum(f.stat().st_size for f in pdf_files if f.exists())
        
        return {
            'total_files': len(pdf_files),
            'total_size_bytes': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'source_directory': str(self.source_dir)
        }


class ProcessingQueue:
    """Manages batch processing with concurrency control."""
    
    def __init__(self, batch_size: int = 10, max_concurrent: int = 3):
        self.batch_size = batch_size
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
    async def process_batch(self, 
                          files: List[Path], 
                          processor_func,
                          progress_tracker: ProgressTracker) -> Dict[str, Any]:
        """
        Process a batch of files with concurrency control.
        
        Args:
            files: List of files to process
            processor_func: Async function to process each file
            progress_tracker: Progress tracker instance
            
        Returns:
            Dictionary with processing results
        """
        results = {
            'processed': 0,
            'failed': 0,
            'errors': []
        }
        
        # Create semaphore-controlled tasks
        async def process_with_semaphore(file_path):
            async with self.semaphore:
                return await processor_func(file_path)
        
        # Process files in batches
        for i in range(0, len(files), self.batch_size):
            batch = files[i:i + self.batch_size]
            
            # Create tasks for this batch
            tasks = [process_with_semaphore(file_path) for file_path in batch]
            
            # Process batch
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Update results and progress
            for j, result in enumerate(batch_results):
                file_path = batch[j]
                
                if isinstance(result, Exception):
                    results['failed'] += 1
                    results['errors'].append({
                        'file': str(file_path),
                        'error': str(result)
                    })
                    logger.error(f"Failed to process {file_path}: {result}")
                else:
                    results['processed'] += 1
                
                # Update progress
                progress_tracker.update_progress(
                    results['processed'] + results['failed'],
                    str(file_path.name)
                )
        
        return results


class ArxivLocalProcessor:
    """Main processor for local arXiv dataset."""
    
    def __init__(self, 
                 source_dir: str = "~/arxiv-dataset/pdf",
                 output_dir: str = "/datapool/aischolar/arxiv-dataset-2024",
                 batch_size: int = 10):
        """
        Initialize ArxivLocalProcessor.
        
        Args:
            source_dir: Source directory containing PDF files
            output_dir: Output directory for processed files and state
            batch_size: Number of files to process in each batch
        """
        self.source_dir = Path(source_dir).expanduser()
        self.output_dir = Path(output_dir)
        self.batch_size = batch_size
        
        # Create output directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.state_dir = self.output_dir / "processed" / "state_files"
        self.error_log_dir = self.output_dir / "processed" / "error_logs"
        
        # Initialize components
        self.processor_id = f"local_processor_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.state_manager = StateManager(self.state_dir)
        self.error_handler = ErrorHandler(self.error_log_dir, self.processor_id)
        self.progress_tracker = ProgressTracker()
        
        # Processing components
        self.pdf_discovery = PDFDiscovery(self.source_dir)
        self.processing_queue = ProcessingQueue(batch_size)
        
        # Statistics
        self.start_time: Optional[datetime] = None
        self.processed_count = 0
        self.failed_count = 0
        
        logger.info(f"ArxivLocalProcessor initialized")
        logger.info(f"Source: {self.source_dir}")
        logger.info(f"Output: {self.output_dir}")
    
    async def initialize_services(self) -> bool:
        """
        Initialize required services for processing.
        
        Returns:
            True if initialization successful, False otherwise
        """
        logger.info("Initializing services...")
        
        try:
            # Check if services are available
            if not all([scientific_pdf_processor, vector_store_service, scientific_rag_service]):
                logger.error("Required services not available")
                return False
            
            # Configure vector store for localhost
            vector_store_service.chroma_host = "localhost"
            vector_store_service.chroma_port = 8082
            
            # Initialize vector store
            await vector_store_service.initialize()
            logger.info("✅ Vector store initialized")
            
            # Check health
            health = await vector_store_service.health_check()
            if health.get('status') != 'healthy':
                logger.warning(f"Vector store health: {health}")
                return False
            
            logger.info("✅ All services initialized successfully")
            return True
            
        except Exception as e:
            self.error_handler.log_error(
                e, 
                {'operation': 'service_initialization'},
                'service_initialization_error'
            )
            logger.error(f"Failed to initialize services: {e}")
            return False
    
    async def process_dataset(self, max_files: Optional[int] = None) -> bool:
        """
        Process the entire dataset.
        
        Args:
            max_files: Maximum number of files to process (None for all)
            
        Returns:
            True if processing completed successfully
        """
        logger.info("Starting dataset processing...")
        self.start_time = datetime.now()
        
        try:
            # Acquire processing lock
            with self.state_manager.get_lock(self.processor_id):
                
                # Discover PDF files
                pdf_files = self.pdf_discovery.discover_pdfs(max_files)
                if not pdf_files:
                    logger.error("No PDF files found to process")
                    return False
                
                # Initialize processing state
                processing_state = ProcessingState(
                    processor_id=self.processor_id,
                    start_time=self.start_time,
                    last_update=self.start_time,
                    total_files=len(pdf_files),
                    processing_stats=ProcessingStats(
                        total_files=len(pdf_files),
                        start_time=self.start_time
                    )
                )
                
                # Start progress tracking
                self.progress_tracker.start_tracking(len(pdf_files))
                
                # Process files
                results = await self.processing_queue.process_batch(
                    pdf_files,
                    self._process_single_pdf,
                    self.progress_tracker
                )
                
                # Update final statistics
                self.processed_count = results['processed']
                self.failed_count = results['failed']
                
                # Update processing state
                processing_state.processed_files = set(
                    str(f) for f in pdf_files[:results['processed']]
                )
                processing_state.processing_stats.processed_count = results['processed']
                processing_state.processing_stats.failed_count = results['failed']
                
                # Save final state
                self.state_manager.save_state(self.processor_id, processing_state)
                
                # Finish progress tracking
                self.progress_tracker.finish("Dataset processing complete")
                
                # Log final summary
                self._log_processing_summary()
                
                return True
                
        except Exception as e:
            self.error_handler.log_error(
                e,
                {'operation': 'dataset_processing'},
                'dataset_processing_error'
            )
            logger.error(f"Dataset processing failed: {e}")
            return False
    
    async def resume_processing(self) -> bool:
        """
        Resume processing from saved state.
        
        Returns:
            True if resume successful, False otherwise
        """
        logger.info("Attempting to resume processing...")
        
        try:
            # Load existing state
            state = self.state_manager.load_state(self.processor_id)
            if not state:
                logger.info("No existing state found, starting fresh processing")
                return await self.process_dataset()
            
            logger.info(f"Found existing state with {len(state.processed_files)} processed files")
            
            # Acquire processing lock
            with self.state_manager.get_lock(self.processor_id):
                
                # Discover all PDF files
                pdf_files = self.pdf_discovery.discover_pdfs()
                if not pdf_files:
                    logger.error("No PDF files found")
                    return False
                
                # Filter out already processed files
                remaining_files = [
                    f for f in pdf_files 
                    if str(f) not in state.processed_files
                ]
                
                if not remaining_files:
                    logger.info("All files already processed")
                    return True
                
                logger.info(f"Resuming with {len(remaining_files)} remaining files")
                
                # Update progress tracker
                already_processed = len(state.processed_files)
                self.progress_tracker.start_tracking(len(pdf_files))
                self.progress_tracker.update_progress(already_processed, "Resuming...")
                
                # Process remaining files
                results = await self.processing_queue.process_batch(
                    remaining_files,
                    self._process_single_pdf,
                    self.progress_tracker
                )
                
                # Update statistics
                self.processed_count = already_processed + results['processed']
                self.failed_count = len(state.failed_files) + results['failed']
                
                # Update state
                state.processed_files.update(str(f) for f in remaining_files[:results['processed']])
                state.processing_stats.processed_count = self.processed_count
                state.processing_stats.failed_count = self.failed_count
                
                # Save updated state
                self.state_manager.save_state(self.processor_id, state)
                
                # Finish progress tracking
                self.progress_tracker.finish("Resume processing complete")
                
                # Log summary
                self._log_processing_summary()
                
                return True
                
        except Exception as e:
            self.error_handler.log_error(
                e,
                {'operation': 'resume_processing'},
                'resume_processing_error'
            )
            logger.error(f"Resume processing failed: {e}")
            return False
    
    async def _process_single_pdf(self, pdf_path: Path) -> bool:
        """
        Process a single PDF file.
        
        Args:
            pdf_path: Path to PDF file to process
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.debug(f"Processing: {pdf_path.name}")
            
            # Extract content from PDF
            document_data = scientific_pdf_processor.extract_comprehensive_content(str(pdf_path))
            
            if not document_data:
                raise ValueError("No content extracted from PDF")
            
            # Create chunks for vector storage
            chunks = scientific_rag_service._create_scientific_chunks(document_data)
            
            if not chunks:
                raise ValueError("No chunks created from document")
            
            # Add to vector store
            result = await vector_store_service.add_document_chunks(
                document_data['document_id'],
                chunks
            )
            
            if not result or result.get('chunks_added', 0) == 0:
                raise ValueError("Failed to add chunks to vector store")
            
            logger.debug(f"Successfully processed {pdf_path.name}: {result.get('chunks_added', 0)} chunks")
            return True
            
        except Exception as e:
            # Log error with context
            context = {
                'file_path': str(pdf_path),
                'file_size': pdf_path.stat().st_size if pdf_path.exists() else 0,
                'operation': 'pdf_processing'
            }
            
            self.error_handler.log_error(e, context, 'pdf_processing_error')
            self.error_handler.log_failed_file(str(pdf_path), str(e))
            
            return False
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Get current processing statistics.
        
        Returns:
            Dictionary with processing statistics
        """
        elapsed_time = None
        if self.start_time:
            elapsed_time = (datetime.now() - self.start_time).total_seconds()
        
        # Get directory stats
        dir_stats = self.pdf_discovery.get_directory_stats()
        
        # Get error summary
        error_summary = self.error_handler.get_error_summary()
        
        return {
            'processor_id': self.processor_id,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'elapsed_time_seconds': elapsed_time,
            'processed_count': self.processed_count,
            'failed_count': self.failed_count,
            'processing_rate': (
                self.processed_count / elapsed_time 
                if elapsed_time and elapsed_time > 0 else 0
            ),
            'directory_stats': dir_stats,
            'error_summary': error_summary.to_dict(),
            'progress_stats': self.progress_tracker.get_stats().to_dict() if self.progress_tracker.is_active() else None
        }
    
    def _log_processing_summary(self) -> None:
        """Log final processing summary."""
        elapsed_time = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        
        logger.info("=" * 60)
        logger.info("PROCESSING SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Processor ID: {self.processor_id}")
        logger.info(f"Source Directory: {self.source_dir}")
        logger.info(f"Output Directory: {self.output_dir}")
        logger.info(f"Total Processed: {self.processed_count}")
        logger.info(f"Total Failed: {self.failed_count}")
        logger.info(f"Success Rate: {(self.processed_count / (self.processed_count + self.failed_count) * 100):.1f}%" if (self.processed_count + self.failed_count) > 0 else "N/A")
        logger.info(f"Processing Time: {elapsed_time/60:.1f} minutes")
        logger.info(f"Average Rate: {(self.processed_count + self.failed_count) / elapsed_time:.2f} files/sec" if elapsed_time > 0 else "N/A")
        logger.info("=" * 60)
        
        # Export error report if there were errors
        if self.failed_count > 0:
            error_report_path = self.error_log_dir / f"{self.processor_id}_final_report.json"
            self.error_handler.export_error_report(error_report_path)
            logger.info(f"Error report saved to: {error_report_path}")
    
    def cleanup(self) -> None:
        """Clean up resources and finalize processing."""
        try:
            # Clear completed state
            self.state_manager.clear_state(self.processor_id)
            
            # Reset progress tracker
            self.progress_tracker.reset()
            
            logger.info("Cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


# Convenience function for direct script execution
async def process_local_dataset(source_dir: str = "~/arxiv-dataset/pdf",
                               output_dir: str = "/datapool/aischolar/arxiv-dataset-2024",
                               max_files: Optional[int] = None,
                               batch_size: int = 10) -> bool:
    """
    Convenience function to process local dataset.
    
    Args:
        source_dir: Source directory containing PDF files
        output_dir: Output directory for processed files
        max_files: Maximum number of files to process
        batch_size: Batch size for processing
        
    Returns:
        True if successful, False otherwise
    """
    processor = ArxivLocalProcessor(source_dir, output_dir, batch_size)
    
    try:
        # Initialize services
        if not await processor.initialize_services():
            logger.error("Failed to initialize services")
            return False
        
        # Process dataset
        success = await processor.process_dataset(max_files)
        
        # Cleanup
        processor.cleanup()
        
        return success
        
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        processor.cleanup()
        return False