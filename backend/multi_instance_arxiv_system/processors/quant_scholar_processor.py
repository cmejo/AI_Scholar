"""
Quant Scholar Processing Pipeline for multi-instance ArXiv system.

Handles PDF processing and vector store integration for Quant Scholar instance:
- PDF content extraction using existing scientific PDF processor
- Document chunking and embedding generation for quantitative research papers
- Vector store integration with separate Quant Scholar collection
- Duplicate detection and skip logic across arXiv and journal sources
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
import json
import hashlib

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from ..shared.multi_instance_data_models import (
    ArxivPaper, JournalPaper, BasePaper, InstanceConfig, ProcessingResult
)

# Import existing services
try:
    from services.scientific_pdf_processor import ScientificPDFProcessor
    from services.vector_store_service import VectorStoreService
except ImportError as e:
    logging.warning(f"Could not import existing services: {e}")
    ScientificPDFProcessor = None
    VectorStoreService = None

logger = logging.getLogger(__name__)


class QuantScholarProcessor:
    """Quant Scholar processor for PDF processing and vector store integration."""
    
    def __init__(self, instance_config: InstanceConfig):
        """
        Initialize Quant Scholar processor.
        
        Args:
            instance_config: Configuration for the Quant Scholar instance
        """
        self.config = instance_config
        self.instance_name = instance_config.instance_name
        
        # Initialize components (will be set during initialization)
        self.pdf_processor: Optional[ScientificPDFProcessor] = None
        self.vector_store = None  # Will use MultiInstanceVectorStoreService from AI Scholar
        self.chunker = None  # Will use ScientificChunker from AI Scholar
        
        # Track processed documents
        self.processed_documents: Set[str] = set()
        
        logger.info(f"QuantScholarProcessor initialized for instance '{self.instance_name}'")
    
    async def initialize(self) -> bool:
        """Initialize the processor components."""
        try:
            # Initialize PDF processor
            if ScientificPDFProcessor:
                self.pdf_processor = ScientificPDFProcessor()
                logger.info("Scientific PDF processor initialized")
            else:
                logger.warning("Scientific PDF processor not available")
                return False
            
            # Import and initialize vector store from AI Scholar processor
            try:
                from ..processors.ai_scholar_processor import MultiInstanceVectorStoreService, ScientificChunker
                
                # Initialize vector store for Quant Scholar
                self.vector_store = MultiInstanceVectorStoreService(
                    self.instance_name,
                    self.config.vector_store_config.to_dict()
                )
                
                success = await self.vector_store.initialize()
                if not success:
                    logger.error("Failed to initialize vector store")
                    return False
                
                logger.info("Vector store initialized")
                
                # Initialize chunker
                self.chunker = ScientificChunker(
                    chunk_size=self.config.vector_store_config.chunk_size,
                    chunk_overlap=self.config.vector_store_config.chunk_overlap
                )
                logger.info("Scientific chunker initialized")
                
            except ImportError as e:
                logger.error(f"Failed to import AI Scholar processor components: {e}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Quant Scholar processor: {e}")
            return False
    
    async def process_papers(self, pdf_paths: List[str]) -> ProcessingResult:
        """
        Process a list of PDF files from multiple source types.
        
        Args:
            pdf_paths: List of PDF file paths to process (arXiv and journal papers)
            
        Returns:
            ProcessingResult with processing statistics
        """
        if not self.pdf_processor or not self.vector_store or not self.chunker:
            raise RuntimeError("Processor not initialized")
        
        result = ProcessingResult()
        
        logger.info(f"Processing {len(pdf_paths)} PDFs for Quant Scholar (arXiv and journal sources)")
        
        # Categorize papers by source type for better logging
        arxiv_papers = []
        journal_papers = []
        
        for pdf_path in pdf_paths:
            filename = Path(pdf_path).stem
            if filename.startswith('jss_') or filename.startswith('rjournal_'):
                journal_papers.append(pdf_path)
            else:
                arxiv_papers.append(pdf_path)
        
        logger.info(f"Processing breakdown: {len(arxiv_papers)} arXiv papers, {len(journal_papers)} journal papers")
        
        # Process all papers
        for pdf_path in pdf_paths:
            try:
                success = await self._process_single_pdf(pdf_path)
                
                if success:
                    result.processed_papers.append(pdf_path)
                else:
                    result.failed_papers.append(pdf_path)
                    
            except Exception as e:
                result.failed_papers.append(pdf_path)
                logger.error(f"Failed to process {pdf_path}: {e}")
        
        logger.info(f"Quant Scholar processing completed: {result.success_count} successful, "
                   f"{result.failure_count} failed")
        
        return result
    
    async def _process_single_pdf(self, pdf_path: str) -> bool:
        """Process a single PDF file with comprehensive error handling for both arXiv and journal papers."""
        try:
            pdf_file = Path(pdf_path)
            if not pdf_file.exists():
                error_msg = f"PDF file not found: {pdf_path}"
                logger.error(error_msg)
                self._log_processing_error(
                    Exception(error_msg),
                    {'pdf_path': pdf_path, 'operation': 'file_validation'},
                    'file_not_found'
                )
                return False
            
            # Extract paper ID from filename (handles both arXiv and journal papers)
            paper_id = self._extract_paper_id_from_path(pdf_path)
            if not paper_id:
                error_msg = f"Could not extract paper ID from {pdf_path}"
                logger.error(error_msg)
                self._log_processing_error(
                    Exception(error_msg),
                    {'pdf_path': pdf_path, 'operation': 'paper_id_extraction'},
                    'metadata_extraction_error'
                )
                return False
            
            # Determine source type
            source_type = self._determine_source_type(pdf_path)
            logger.debug(f"Processing {source_type} paper: {paper_id}")
            
            # Check if already processed (unified duplicate detection across sources)
            if paper_id in self.processed_documents:
                logger.debug(f"Skipping already processed paper: {paper_id}")
                return True
            
            # Extract content from PDF with error handling
            logger.debug(f"Extracting content from {pdf_path}")
            try:
                content = self.pdf_processor.extract_comprehensive_content(pdf_path)
            except Exception as e:
                self._log_processing_error(
                    e,
                    {'pdf_path': pdf_path, 'paper_id': paper_id, 'operation': 'pdf_extraction'},
                    'pdf_processing_error'
                )
                logger.error(f"Failed to extract content from {pdf_path}: {e}")
                return False
            
            if not content or not content.get('full_text'):
                error_msg = f"No text extracted from {pdf_path}"
                logger.warning(error_msg)
                self._log_processing_error(
                    Exception(error_msg),
                    {'pdf_path': pdf_path, 'paper_id': paper_id, 'operation': 'content_validation'},
                    'empty_content_error'
                )
                return False
            
            # Create paper object from extracted metadata
            try:
                paper = self._create_paper_from_content(content, paper_id, pdf_path, source_type)
            except Exception as e:
                self._log_processing_error(
                    e,
                    {'pdf_path': pdf_path, 'paper_id': paper_id, 'operation': 'paper_object_creation'},
                    'metadata_processing_error'
                )
                logger.error(f"Failed to create paper object for {paper_id}: {e}")
                return False
            
            # Create document chunks with error handling
            logger.debug(f"Creating chunks for {paper_id}")
            try:
                chunks = self.chunker.create_scientific_chunks(content, paper)
            except Exception as e:
                self._log_processing_error(
                    e,
                    {'pdf_path': pdf_path, 'paper_id': paper_id, 'operation': 'chunking'},
                    'chunking_error'
                )
                logger.error(f"Failed to create chunks for {paper_id}: {e}")
                return False
            
            if not chunks:
                error_msg = f"No chunks created for {pdf_path}"
                logger.warning(error_msg)
                self._log_processing_error(
                    Exception(error_msg),
                    {'pdf_path': pdf_path, 'paper_id': paper_id, 'operation': 'chunk_validation'},
                    'empty_chunks_error'
                )
                return False
            
            # Add to vector store with error handling
            logger.debug(f"Adding {len(chunks)} chunks to vector store for {paper_id}")
            try:
                await self.vector_store.add_instance_document(paper, chunks)
            except Exception as e:
                self._log_processing_error(
                    e,
                    {'pdf_path': pdf_path, 'paper_id': paper_id, 'chunks_count': len(chunks), 'operation': 'vector_store_addition'},
                    'vector_store_error'
                )
                logger.error(f"Failed to add {paper_id} to vector store: {e}")
                return False
            
            # Mark as processed
            self.processed_documents.add(paper_id)
            
            logger.info(f"Successfully processed {paper_id} with {len(chunks)} chunks")
            return True
            
        except Exception as e:
            self._log_processing_error(
                e,
                {'pdf_path': pdf_path, 'operation': 'general_processing'},
                'general_processing_error'
            )
            logger.error(f"Unexpected error processing {pdf_path}: {e}")
            return False
    
    def _log_processing_error(self, 
                            error: Exception, 
                            context: Dict[str, Any], 
                            error_type: str) -> None:
        """Log processing error with context."""
        # Enhanced context with processor information
        enhanced_context = context.copy()
        enhanced_context.update({
            'instance_name': self.instance_name,
            'processor_type': 'quant_scholar_processor',
            'timestamp': datetime.now().isoformat(),
            'processed_documents_count': len(self.processed_documents)
        })
        
        # Log error (this could be enhanced to use Quant Scholar error handler if available)
        logger.error(f"Processing error [{error_type}]: {error}", extra=enhanced_context)
    
    def _determine_source_type(self, pdf_path: str) -> str:
        """Determine the source type of the paper from the file path."""
        filename = Path(pdf_path).stem
        if filename.startswith('jss_'):
            return 'journal_jss'
        elif filename.startswith('rjournal_'):
            return 'journal_rjournal'
        else:
            return 'arxiv'
    
    def _extract_paper_id_from_path(self, pdf_path: str) -> Optional[str]:
        """Extract paper ID from PDF file path (handles both arXiv and journal papers)."""
        try:
            filename = Path(pdf_path).stem
            
            # Handle journal paper IDs
            if filename.startswith('jss_') or filename.startswith('rjournal_'):
                return filename
            else:
                # Assume arXiv ID format
                parts = filename.split('_')
                if len(parts) > 0:
                    # Convert back from safe filename format
                    paper_id = parts[0].replace('_', '/')
                    return paper_id
        except Exception:
            pass
        return None
    
    def _create_paper_from_content(self, 
                                 content: Dict[str, Any], 
                                 paper_id: str,
                                 pdf_path: str,
                                 source_type: str) -> Any:
        """Create paper object from extracted content (ArxivPaper or JournalPaper)."""
        metadata = content.get('metadata', {})
        sections = content.get('sections', {})
        
        # Extract title (from metadata or first section)
        title = metadata.get('title', '')
        if not title and sections.get('title'):
            title = sections['title'][:200]  # Limit title length
        
        # Extract authors
        authors = metadata.get('authors', [])
        if isinstance(authors, str):
            authors = [authors]
        
        # Extract abstract
        abstract = sections.get('abstract', '')[:2000]  # Limit abstract length
        
        # Create paper object based on source type
        if source_type.startswith('journal'):
            # Create JournalPaper object
            if source_type == 'journal_jss':
                journal_name = "Journal of Statistical Software"
                journal_url = "https://www.jstatsoft.org/"
            elif source_type == 'journal_rjournal':
                journal_name = "The R Journal"
                journal_url = "https://journal.r-project.org/"
            else:
                journal_name = "Unknown Journal"
                journal_url = ""
            
            # Extract volume/issue from paper_id
            parts = paper_id.split('_')
            volume = parts[1] if len(parts) > 1 else "unknown"
            issue = parts[2] if len(parts) > 2 else "unknown"
            
            from ..shared.multi_instance_data_models import JournalPaper
            paper = JournalPaper(
                paper_id=paper_id,
                title=title or f"Paper {paper_id}",
                authors=authors or ['Unknown'],
                abstract=abstract or 'No abstract available',
                published_date=datetime.now(),  # Would need to be extracted from metadata
                source_type='journal',
                instance_name=self.instance_name,
                journal_name=journal_name,
                volume=volume,
                issue=issue,
                pdf_url=f"file://{pdf_path}",
                journal_url=journal_url,
                metadata={
                    'extracted_from_pdf': True,
                    'processing_timestamp': datetime.now().isoformat(),
                    'file_path': pdf_path,
                    'extraction_quality': content.get('extraction_quality', 'unknown'),
                    'source_handler': source_type
                }
            )
        else:
            # Create ArxivPaper object
            from ..shared.multi_instance_data_models import ArxivPaper
            
            # Try to extract categories from metadata or filename
            categories = metadata.get('categories', [])
            if not categories:
                # Try to infer from Quant Scholar categories
                categories = self._infer_arxiv_categories(paper_id, content)
            
            paper = ArxivPaper(
                paper_id=paper_id,
                title=title or f"Paper {paper_id}",
                authors=authors or ['Unknown'],
                abstract=abstract or 'No abstract available',
                published_date=datetime.now(),  # Would need to be extracted from metadata
                source_type='arxiv',
                instance_name=self.instance_name,
                arxiv_id=paper_id,
                categories=categories,
                pdf_url=f"https://arxiv.org/pdf/{paper_id}.pdf",
                metadata={
                    'extracted_from_pdf': True,
                    'processing_timestamp': datetime.now().isoformat(),
                    'file_path': pdf_path,
                    'extraction_quality': content.get('extraction_quality', 'unknown')
                }
            )
        
        return paper
    
    def _infer_arxiv_categories(self, paper_id: str, content: Dict[str, Any]) -> List[str]:
        """Infer arXiv categories for Quant Scholar papers based on content analysis."""
        # Default Quant Scholar categories
        quant_categories = [
            'econ.EM', 'econ.GN', 'econ.TH', 'eess.SY', 
            'math.ST', 'math.PR', 'math.OC', 'q-fin.CP', 
            'q-fin.EC', 'q-fin.GN', 'q-fin.MF', 'q-fin.PM', 
            'q-fin.PR', 'q-fin.RM', 'q-fin.ST', 'q-fin.TR',
            'stat.AP', 'stat.CO', 'stat.ME', 'stat.ML', 'stat.TH'
        ]
        
        # Try to extract from paper ID if it contains category info
        if '.' in paper_id:
            potential_category = paper_id.split('.')[0]
            if potential_category in ['econ', 'eess', 'math', 'q-fin', 'stat']:
                # Look for more specific category
                for cat in quant_categories:
                    if cat.startswith(potential_category):
                        return [cat]
        
        # Analyze content for category hints
        full_text = content.get('full_text', '').lower()
        abstract = content.get('sections', {}).get('abstract', '').lower()
        text_to_analyze = abstract + ' ' + full_text[:1000]  # First 1000 chars
        
        # Category keywords mapping
        category_keywords = {
            'q-fin.ST': ['statistics', 'statistical', 'econometrics', 'time series'],
            'q-fin.CP': ['computational', 'pricing', 'derivatives', 'options'],
            'q-fin.RM': ['risk', 'management', 'var', 'value at risk'],
            'q-fin.PM': ['portfolio', 'optimization', 'asset allocation'],
            'stat.ML': ['machine learning', 'neural network', 'deep learning'],
            'stat.AP': ['applied statistics', 'statistical analysis'],
            'math.ST': ['probability', 'stochastic', 'mathematical statistics'],
            'econ.EM': ['empirical', 'econometric', 'regression']
        }
        
        # Find matching categories
        matched_categories = []
        for category, keywords in category_keywords.items():
            if any(keyword in text_to_analyze for keyword in keywords):
                matched_categories.append(category)
        
        # Return matched categories or default
        return matched_categories if matched_categories else ['q-fin.GN']  # General quantitative finance
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics with source type breakdown."""
        # Analyze processed documents by source type
        arxiv_count = 0
        journal_count = 0
        
        for doc_id in self.processed_documents:
            if doc_id.startswith('jss_') or doc_id.startswith('rjournal_'):
                journal_count += 1
            else:
                arxiv_count += 1
        
        stats = {
            'instance_name': self.instance_name,
            'total_processed_documents': len(self.processed_documents),
            'source_breakdown': {
                'arxiv_papers': arxiv_count,
                'journal_papers': journal_count,
                'journal_sources': ['Journal of Statistical Software', 'The R Journal']
            },
            'processor_initialized': all([
                self.pdf_processor is not None,
                self.vector_store is not None,
                self.chunker is not None
            ]),
            'unified_processing': True,  # Indicates support for multiple source types
            'duplicate_detection': 'cross_source'  # Indicates duplicate detection across sources
        }
        
        # Add vector store stats if available
        if self.vector_store:
            try:
                vector_stats = self.vector_store.get_instance_stats()
                stats['vector_store'] = vector_stats
            except Exception as e:
                stats['vector_store_error'] = str(e)
        
        return stats
    
    def load_processed_documents(self, processed_list: List[str]) -> None:
        """Load list of already processed documents."""
        self.processed_documents.update(processed_list)
        logger.info(f"Loaded {len(processed_list)} processed documents")
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get processing error summary."""
        return {
            'instance_name': self.instance_name,
            'processor_type': 'quant_scholar_processor',
            'processed_documents_count': len(self.processed_documents),
            'components_initialized': {
                'pdf_processor': self.pdf_processor is not None,
                'vector_store': self.vector_store is not None,
                'chunker': self.chunker is not None
            },
            'last_updated': datetime.now().isoformat()
        }
    
    def should_continue_processing(self, max_error_rate: float = 35.0) -> bool:
        """Determine if processing should continue based on error patterns."""
        # Check if all components are initialized
        if not all([self.pdf_processor, self.vector_store, self.chunker]):
            logger.error("Not all processor components are initialized")
            return False
        
        # Additional checks could be added here based on error rates
        return True
    
    async def validate_processing_environment(self) -> bool:
        """Validate that the processing environment is ready."""
        try:
            # Check PDF processor
            if not self.pdf_processor:
                logger.error("PDF processor not initialized")
                return False
            
            # Check vector store
            if not self.vector_store:
                logger.error("Vector store not initialized")
                return False
            
            # Test vector store connection
            try:
                stats = self.vector_store.get_instance_stats()
                if 'error' in stats:
                    logger.error(f"Vector store error: {stats['error']}")
                    return False
            except Exception as e:
                logger.error(f"Failed to get vector store stats: {e}")
                return False
            
            # Check chunker
            if not self.chunker:
                logger.error("Chunker not initialized")
                return False
            
            logger.info("Processing environment validation successful")
            return True
            
        except Exception as e:
            logger.error(f"Processing environment validation failed: {e}")
            return False
    
    def export_processing_report(self, output_path: Path) -> bool:
        """Export comprehensive processing report."""
        try:
            report = {
                'report_type': 'quant_scholar_processor_report',
                'generated_at': datetime.now().isoformat(),
                'processor_stats': self.get_processing_stats(),
                'error_summary': self.get_error_summary(),
                'configuration': {
                    'instance_name': self.instance_name,
                    'chunk_size': self.chunker.chunk_size if self.chunker else None,
                    'chunk_overlap': self.chunker.chunk_overlap if self.chunker else None
                }
            }
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Processing report exported to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export processing report: {e}")
            return False
    
    def shutdown(self) -> None:
        """Shutdown the processor."""
        logger.info(f"Shutting down Quant Scholar processor for '{self.instance_name}'")
        
        # Clear processed documents
        self.processed_documents.clear()
        
        # Reset components
        self.pdf_processor = None
        self.vector_store = None
        self.chunker = None
        
        logger.info("Quant Scholar processor shutdown complete")