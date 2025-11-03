"""
AI Scholar Processing Pipeline for multi-instance ArXiv system.

Handles PDF processing and vector store integration for AI Scholar instance:
- PDF content extraction using existing scientific PDF processor
- Document chunking and embedding generation
- Vector store integration with separate AI Scholar collection
- Duplicate detection and skip logic
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
    ArxivPaper, InstanceConfig, ProcessingResult
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


class MultiInstanceVectorStoreService:
    """Extended vector store service for multi-instance support."""
    
    def __init__(self, instance_name: str, vector_store_config: Dict[str, Any]):
        """
        Initialize multi-instance vector store service.
        
        Args:
            instance_name: Name of the scholar instance
            vector_store_config: Vector store configuration
        """
        self.instance_name = instance_name
        self.config = vector_store_config
        self.collection_name = vector_store_config.get('collection_name', f"{instance_name}_papers")
        
        # Initialize base vector store service
        self.base_service = VectorStoreService(
            chroma_host=vector_store_config.get('host', 'localhost'),
            chroma_port=vector_store_config.get('port', 8082)
        )
        
        # Override collection name for instance separation
        self.base_service.collection_name = self.collection_name
        
        logger.info(f"MultiInstanceVectorStoreService initialized for '{instance_name}' "
                   f"with collection '{self.collection_name}'")
    
    async def initialize(self) -> bool:
        """Initialize the vector store service."""
        try:
            await self.base_service.initialize()
            
            # Update collection metadata with instance information (excluding distance function)
            if self.base_service.collection:
                try:
                    # Get current metadata and preserve distance function settings
                    current_metadata = self.base_service.collection.metadata or {}
                    
                    # Create new metadata without modifying distance function
                    new_metadata = {
                        key: value for key, value in current_metadata.items()
                        if not key.startswith('hnsw:')  # Preserve HNSW settings
                    }
                    
                    # Add instance-specific metadata
                    new_metadata.update({
                        "instance_name": self.instance_name,
                        "instance_type": "ai_scholar" if "ai" in self.instance_name.lower() else "quant_scholar",
                        "last_updated": datetime.now().isoformat()
                    })
                    
                    # Only modify if we have new metadata to add
                    if new_metadata != current_metadata:
                        # Preserve HNSW settings from current metadata
                        for key, value in current_metadata.items():
                            if key.startswith('hnsw:'):
                                new_metadata[key] = value
                        
                        self.base_service.collection.modify(metadata=new_metadata)
                        logger.info(f"Updated collection metadata for instance '{self.instance_name}'")
                    else:
                        logger.info(f"Collection metadata already up to date for instance '{self.instance_name}'")
                        
                except Exception as metadata_error:
                    # If metadata update fails, log warning but continue
                    logger.warning(f"Could not update collection metadata for '{self.instance_name}': {metadata_error}")
                    logger.info("Continuing with existing collection metadata")
            
            logger.info(f"Vector store initialized for instance '{self.instance_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize vector store for '{self.instance_name}': {e}")
            return False
    
    async def add_instance_document(self, 
                                  paper: Any,  # Can be ArxivPaper or JournalPaper
                                  chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Add document chunks to the instance-specific collection.
        
        Args:
            paper: ArxivPaper or JournalPaper object with metadata
            chunks: List of document chunks
            
        Returns:
            Dictionary with addition results
        """
        try:
            # Enhance chunks with instance-specific metadata
            enhanced_chunks = []
            for chunk in chunks:
                enhanced_chunk = chunk.copy()
                
                # Add instance metadata (handle both ArxivPaper and JournalPaper)
                document_metadata = {
                    'instance_name': self.instance_name,
                    'paper_id': paper.paper_id,
                    'title': paper.title,
                    'authors': paper.authors,
                    'published_date': paper.published_date.isoformat(),
                    'source_type': paper.source_type,
                    'pdf_url': getattr(paper, 'pdf_url', ''),
                    'doi': getattr(paper, 'doi', None)
                }
                
                # Add source-specific metadata
                if hasattr(paper, 'arxiv_id'):  # ArxivPaper
                    document_metadata.update({
                        'arxiv_id': paper.arxiv_id,
                        'categories': getattr(paper, 'categories', [])
                    })
                elif hasattr(paper, 'journal_name'):  # JournalPaper
                    document_metadata.update({
                        'journal_name': paper.journal_name,
                        'volume': getattr(paper, 'volume', None),
                        'issue': getattr(paper, 'issue', None),
                        'pages': getattr(paper, 'pages', None),
                        'journal_url': getattr(paper, 'journal_url', '')
                    })
                
                enhanced_chunk['document_metadata'] = document_metadata
                
                # Add processing metadata
                enhanced_chunk['processing_metadata'] = {
                    'processed_at': datetime.now().isoformat(),
                    'processor_version': '1.0.0',
                    'instance_collection': self.collection_name
                }
                
                enhanced_chunks.append(enhanced_chunk)
            
            # Use base service to add chunks
            document_id = paper.get_document_id()
            result = await self.base_service.add_document_chunks(document_id, enhanced_chunks)
            
            logger.info(f"Added document '{document_id}' to collection '{self.collection_name}' "
                       f"with {result.get('chunks_added', 0)} chunks")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to add document to instance collection: {e}")
            raise
    
    async def search_instance_papers(self, 
                                   query: str, 
                                   n_results: int = 10,
                                   filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Search papers in the instance-specific collection.
        
        Args:
            query: Search query
            n_results: Number of results to return
            filters: Additional filters
            
        Returns:
            List of search results
        """
        try:
            # Add instance filter
            instance_filters = {'instance_name': self.instance_name}
            if filters:
                instance_filters.update(filters)
            
            results = await self.base_service.semantic_search(
                query=query,
                n_results=n_results,
                filters=instance_filters,
                include_metadata=True
            )
            
            logger.debug(f"Search in '{self.collection_name}' returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Failed to search instance collection: {e}")
            raise
    
    def get_instance_stats(self) -> Dict[str, Any]:
        """Get statistics for the instance collection."""
        try:
            if not self.base_service.collection:
                return {'error': 'Collection not initialized'}
            
            # Get collection count
            count = self.base_service.collection.count()
            
            # Get collection metadata
            metadata = self.base_service.collection.metadata or {}
            
            return {
                'instance_name': self.instance_name,
                'collection_name': self.collection_name,
                'document_count': count,
                'embedding_model': metadata.get('embedding_model', 'unknown'),
                'created_at': metadata.get('created_at'),
                'last_updated': metadata.get('last_updated'),
                'instance_type': metadata.get('instance_type', 'unknown')
            }
            
        except Exception as e:
            logger.error(f"Failed to get instance stats: {e}")
            return {'error': str(e)}


class ScientificChunker:
    """Scientific document chunker optimized for research papers."""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize scientific chunker.
        
        Args:
            chunk_size: Target size for chunks in characters
            chunk_overlap: Overlap between chunks in characters
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Section priorities for chunking
        self.section_priorities = {
            'abstract': 1,
            'introduction': 2,
            'methods': 3,
            'results': 4,
            'discussion': 5,
            'conclusion': 6,
            'references': 7
        }
    
    def create_scientific_chunks(self, 
                               content: Dict[str, Any],
                               paper: Any) -> List[Dict[str, Any]]:
        """
        Create chunks from scientific document content.
        
        Args:
            content: Extracted document content from PDF processor
            paper: ArxivPaper or JournalPaper object with metadata
            
        Returns:
            List of document chunks
        """
        chunks = []
        
        try:
            sections = content.get('sections', {})
            full_text = content.get('full_text', '')
            
            # Create abstract chunk (high priority)
            if sections.get('abstract'):
                abstract_chunk = self._create_chunk(
                    text=sections['abstract'],
                    section='abstract',
                    chunk_type='abstract',
                    paper=paper,
                    chunk_index=len(chunks)
                )
                chunks.append(abstract_chunk)
            
            # Create section-based chunks
            for section_name, section_text in sections.items():
                if section_name == 'abstract':
                    continue  # Already processed
                
                if not section_text or len(section_text.strip()) < 100:
                    continue  # Skip very short sections
                
                section_chunks = self._chunk_section(
                    text=section_text,
                    section=section_name,
                    paper=paper,
                    start_index=len(chunks)
                )
                chunks.extend(section_chunks)
            
            # If no sections found, chunk the full text
            if not chunks and full_text:
                text_chunks = self._chunk_text(
                    text=full_text,
                    section='full_document',
                    paper=paper,
                    start_index=0
                )
                chunks.extend(text_chunks)
            
            # Add metadata to all chunks
            for i, chunk in enumerate(chunks):
                chunk['chunk_id'] = f"{paper.get_document_id()}_chunk_{i}"
                chunk['total_chunks'] = len(chunks)
                chunk['document_stats'] = content.get('statistics', {})
            
            paper_id = getattr(paper, 'arxiv_id', None) or getattr(paper, 'paper_id', 'unknown')
            logger.info(f"Created {len(chunks)} chunks for paper '{paper_id}'")
            return chunks
            
        except Exception as e:
            paper_id = getattr(paper, 'arxiv_id', None) or getattr(paper, 'paper_id', 'unknown')
            logger.error(f"Failed to create chunks for paper '{paper_id}': {e}")
            return []
    
    def _create_chunk(self, 
                     text: str,
                     section: str,
                     chunk_type: str,
                     paper: Any,
                     chunk_index: int) -> Dict[str, Any]:
        """Create a single chunk with metadata."""
        # Create base paper metadata
        paper_metadata = {
            'paper_id': paper.paper_id,
            'title': paper.title,
            'authors': paper.authors,
            'published_date': paper.published_date.isoformat(),
            'source_type': paper.source_type
        }
        
        # Add source-specific metadata
        if hasattr(paper, 'arxiv_id'):  # ArxivPaper
            paper_metadata.update({
                'arxiv_id': paper.arxiv_id,
                'categories': getattr(paper, 'categories', [])
            })
        elif hasattr(paper, 'journal_name'):  # JournalPaper
            paper_metadata.update({
                'journal_name': paper.journal_name,
                'volume': getattr(paper, 'volume', None),
                'issue': getattr(paper, 'issue', None)
            })
        
        return {
            'text': text.strip(),
            'section': section,
            'chunk_type': chunk_type,
            'chunk_index': chunk_index,
            'word_count': len(text.split()),
            'character_count': len(text),
            'priority': self.section_priorities.get(section, 10),
            'paper_metadata': paper_metadata
        }
    
    def _chunk_section(self, 
                      text: str,
                      section: str,
                      paper: Any,
                      start_index: int) -> List[Dict[str, Any]]:
        """Chunk a section of text."""
        if len(text) <= self.chunk_size:
            # Section fits in one chunk
            return [self._create_chunk(
                text=text,
                section=section,
                chunk_type='section',
                paper=paper,
                chunk_index=start_index
            )]
        
        # Split section into multiple chunks
        return self._chunk_text(text, section, paper, start_index)
    
    def _chunk_text(self, 
                   text: str,
                   section: str,
                   paper: Any,
                   start_index: int) -> List[Dict[str, Any]]:
        """Split text into overlapping chunks."""
        chunks = []
        
        # Split by sentences first
        sentences = self._split_sentences(text)
        
        current_chunk = ""
        current_sentences = []
        
        for sentence in sentences:
            # Check if adding this sentence would exceed chunk size
            if (len(current_chunk) + len(sentence) > self.chunk_size and 
                current_chunk):
                
                # Create chunk from current content
                chunk = self._create_chunk(
                    text=current_chunk,
                    section=section,
                    chunk_type='text_chunk',
                    paper=paper,
                    chunk_index=start_index + len(chunks)
                )
                chunks.append(chunk)
                
                # Start new chunk with overlap
                overlap_text = self._create_overlap(current_sentences)
                current_chunk = overlap_text + sentence
                current_sentences = [sentence]
            else:
                current_chunk += sentence
                current_sentences.append(sentence)
        
        # Add final chunk if there's remaining content
        if current_chunk.strip():
            chunk = self._create_chunk(
                text=current_chunk,
                section=section,
                chunk_type='text_chunk',
                paper=paper,
                chunk_index=start_index + len(chunks)
            )
            chunks.append(chunk)
        
        return chunks
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting (could be enhanced with NLTK)
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() + ' ' for s in sentences if s.strip()]
    
    def _create_overlap(self, sentences: List[str]) -> str:
        """Create overlap text from recent sentences."""
        if not sentences:
            return ""
        
        overlap_text = ""
        for sentence in reversed(sentences):
            if len(overlap_text) + len(sentence) <= self.chunk_overlap:
                overlap_text = sentence + overlap_text
            else:
                break
        
        return overlap_text


class AIScholarProcessor:
    """AI Scholar processor for PDF processing and vector store integration."""
    
    def __init__(self, instance_config: InstanceConfig):
        """
        Initialize AI Scholar processor.
        
        Args:
            instance_config: Configuration for the AI Scholar instance
        """
        self.config = instance_config
        self.instance_name = instance_config.instance_name
        
        # Initialize components
        self.pdf_processor: Optional[ScientificPDFProcessor] = None
        self.vector_store: Optional[MultiInstanceVectorStoreService] = None
        self.chunker: Optional[ScientificChunker] = None
        
        # Track processed documents
        self.processed_documents: Set[str] = set()
        
        logger.info(f"AIScholarProcessor initialized for instance '{self.instance_name}'")
    
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
            
            # Initialize vector store
            if VectorStoreService:
                self.vector_store = MultiInstanceVectorStoreService(
                    self.instance_name,
                    self.config.vector_store_config.to_dict()
                )
                
                success = await self.vector_store.initialize()
                if not success:
                    logger.error("Failed to initialize vector store")
                    return False
                
                logger.info("Vector store initialized")
            else:
                logger.warning("Vector store service not available")
                return False
            
            # Initialize chunker
            self.chunker = ScientificChunker(
                chunk_size=self.config.vector_store_config.chunk_size,
                chunk_overlap=self.config.vector_store_config.chunk_overlap
            )
            logger.info("Scientific chunker initialized")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize AI Scholar processor: {e}")
            return False
    
    async def process_papers(self, pdf_paths: List[str]) -> ProcessingResult:
        """
        Process a list of PDF files.
        
        Args:
            pdf_paths: List of PDF file paths to process
            
        Returns:
            ProcessingResult with processing statistics
        """
        if not self.pdf_processor or not self.vector_store or not self.chunker:
            raise RuntimeError("Processor not initialized")
        
        result = ProcessingResult()
        
        logger.info(f"Processing {len(pdf_paths)} PDFs for AI Scholar")
        
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
        
        logger.info(f"Processing completed: {result.success_count} successful, "
                   f"{result.failure_count} failed")
        
        return result
    
    async def _process_single_pdf(self, pdf_path: str) -> bool:
        """Process a single PDF file with comprehensive error handling."""
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
            
            # Extract arXiv ID from filename
            arxiv_id = self._extract_arxiv_id_from_path(pdf_path)
            if not arxiv_id:
                error_msg = f"Could not extract arXiv ID from {pdf_path}"
                logger.error(error_msg)
                self._log_processing_error(
                    Exception(error_msg),
                    {'pdf_path': pdf_path, 'operation': 'arxiv_id_extraction'},
                    'metadata_extraction_error'
                )
                return False
            
            # Check if already processed
            if arxiv_id in self.processed_documents:
                logger.debug(f"Skipping already processed paper: {arxiv_id}")
                return True
            
            # Extract content from PDF with error handling
            logger.debug(f"Extracting content from {pdf_path}")
            try:
                content = self.pdf_processor.extract_comprehensive_content(pdf_path)
            except Exception as e:
                self._log_processing_error(
                    e,
                    {'pdf_path': pdf_path, 'arxiv_id': arxiv_id, 'operation': 'pdf_extraction'},
                    'pdf_processing_error'
                )
                logger.error(f"Failed to extract content from {pdf_path}: {e}")
                return False
            
            if not content or not content.get('full_text'):
                error_msg = f"No text extracted from {pdf_path}"
                logger.warning(error_msg)
                self._log_processing_error(
                    Exception(error_msg),
                    {'pdf_path': pdf_path, 'arxiv_id': arxiv_id, 'operation': 'content_validation'},
                    'empty_content_error'
                )
                return False
            
            # Create ArxivPaper object from extracted metadata
            try:
                paper = self._create_arxiv_paper_from_content(content, arxiv_id)
            except Exception as e:
                self._log_processing_error(
                    e,
                    {'pdf_path': pdf_path, 'arxiv_id': arxiv_id, 'operation': 'paper_object_creation'},
                    'metadata_processing_error'
                )
                logger.error(f"Failed to create paper object for {arxiv_id}: {e}")
                return False
            
            # Create document chunks with error handling
            logger.debug(f"Creating chunks for {arxiv_id}")
            try:
                chunks = self.chunker.create_scientific_chunks(content, paper)
            except Exception as e:
                self._log_processing_error(
                    e,
                    {'pdf_path': pdf_path, 'arxiv_id': arxiv_id, 'operation': 'chunking'},
                    'chunking_error'
                )
                logger.error(f"Failed to create chunks for {arxiv_id}: {e}")
                return False
            
            if not chunks:
                error_msg = f"No chunks created for {pdf_path}"
                logger.warning(error_msg)
                self._log_processing_error(
                    Exception(error_msg),
                    {'pdf_path': pdf_path, 'arxiv_id': arxiv_id, 'operation': 'chunk_validation'},
                    'empty_chunks_error'
                )
                return False
            
            # Add to vector store with error handling
            logger.debug(f"Adding {len(chunks)} chunks to vector store for {arxiv_id}")
            try:
                await self.vector_store.add_instance_document(paper, chunks)
            except Exception as e:
                self._log_processing_error(
                    e,
                    {'pdf_path': pdf_path, 'arxiv_id': arxiv_id, 'chunks_count': len(chunks), 'operation': 'vector_store_addition'},
                    'vector_store_error'
                )
                logger.error(f"Failed to add {arxiv_id} to vector store: {e}")
                return False
            
            # Mark as processed
            self.processed_documents.add(arxiv_id)
            
            logger.info(f"Successfully processed {arxiv_id} with {len(chunks)} chunks")
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
            'processor_type': 'ai_scholar_processor',
            'timestamp': datetime.now().isoformat(),
            'processed_documents_count': len(self.processed_documents)
        })
        
        # Log error (this could be enhanced to use AI Scholar error handler if available)
        logger.error(f"Processing error [{error_type}]: {error}", extra=enhanced_context)
    
    def _extract_arxiv_id_from_path(self, pdf_path: str) -> Optional[str]:
        """Extract arXiv ID from PDF file path."""
        try:
            filename = Path(pdf_path).stem
            # Assume filename starts with arXiv ID
            parts = filename.split('_')
            if len(parts) > 0:
                # Convert back from safe filename format
                arxiv_id = parts[0].replace('_', '/')
                return arxiv_id
        except Exception:
            pass
        return None
    
    def _create_arxiv_paper_from_content(self, 
                                       content: Dict[str, Any], 
                                       arxiv_id: str) -> ArxivPaper:
        """Create ArxivPaper object from extracted content."""
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
        
        # Create paper object
        paper = ArxivPaper(
            paper_id=arxiv_id,
            title=title or f"Paper {arxiv_id}",
            authors=authors or ['Unknown'],
            abstract=abstract or 'No abstract available',
            published_date=datetime.now(),  # Would need to be extracted from metadata
            source_type='arxiv',
            instance_name=self.instance_name,
            arxiv_id=arxiv_id,
            categories=[],  # Would need to be extracted from metadata
            pdf_url=f"https://arxiv.org/pdf/{arxiv_id}.pdf",
            metadata={
                'extracted_from_pdf': True,
                'processing_timestamp': datetime.now().isoformat(),
                'file_path': content.get('file_path', ''),
                'extraction_quality': content.get('extraction_quality', 'unknown')
            }
        )
        
        return paper
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        stats = {
            'instance_name': self.instance_name,
            'processed_documents': len(self.processed_documents),
            'processor_initialized': all([
                self.pdf_processor is not None,
                self.vector_store is not None,
                self.chunker is not None
            ])
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
            'processor_type': 'ai_scholar_processor',
            'processed_documents_count': len(self.processed_documents),
            'components_initialized': {
                'pdf_processor': self.pdf_processor is not None,
                'vector_store': self.vector_store is not None,
                'chunker': self.chunker is not None
            },
            'last_updated': datetime.now().isoformat()
        }
    
    def should_continue_processing(self, max_error_rate: float = 30.0) -> bool:
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
                'report_type': 'ai_scholar_processor_report',
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
        logger.info(f"Shutting down AI Scholar processor for '{self.instance_name}'")
        
        # Clear processed documents
        self.processed_documents.clear()
        
        # Reset components
        self.pdf_processor = None
        self.vector_store = None
        self.chunker = None
        
        logger.info("AI Scholar processor shutdown complete")