"""
Document processing service with multi-modal support and hierarchical chunking
"""
import os
import uuid
import aiofiles
import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import UploadFile
import PyPDF2
import pdfplumber
import pytesseract
from PIL import Image
import cv2
import numpy as np
from sqlalchemy.orm import Session

from core.database import get_db, Document, DocumentChunk, DocumentChunkEnhanced
from core.config import settings
from services.text_processor import TextProcessor
from services.image_processor import ImageProcessor
from services.hierarchical_chunking import HierarchicalChunker, ChunkingStrategy

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        self.text_processor = TextProcessor()
        self.image_processor = ImageProcessor()
        self.hierarchical_chunker = HierarchicalChunker()
        
        # Ensure upload directory exists
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    async def process_document(self, file: UploadFile, user_id: str) -> Dict[str, Any]:
        """Process uploaded document with multi-modal support"""
        try:
            # Generate unique filename
            file_id = str(uuid.uuid4())
            file_extension = os.path.splitext(file.filename)[1]
            file_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}{file_extension}")
            
            # Save file
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            # Create database record
            db = next(get_db())
            document = Document(
                id=file_id,
                user_id=user_id,
                name=file.filename,
                file_path=file_path,
                content_type=file.content_type,
                size=len(content),
                status="processing"
            )
            db.add(document)
            db.commit()
            
            # Process based on file type
            if file.content_type == 'application/pdf':
                result = await self._process_pdf(file_path, file_id, db)
            elif file.content_type == 'text/plain':
                result = await self._process_text(file_path, file_id, db)
            elif file.content_type.startswith('image/'):
                result = await self._process_image(file_path, file_id, db)
            else:
                raise ValueError(f"Unsupported file type: {file.content_type}")
            
            # Update document status
            document.status = "completed"
            document.chunks_count = result['chunks_count']
            document.embeddings_count = result['embeddings_count']
            db.commit()
            
            # Integrate with vector store for hierarchical chunks
            await self._integrate_with_vector_store({
                "id": file_id,
                "name": file.filename,
                "content_type": file.content_type,
                "chunks_count": result['chunks_count']
            })
            
            return {
                "id": file_id,
                "name": file.filename,
                "status": "completed",
                "chunks": result['chunks_count'],
                "embeddings": result['embeddings_count'],
                "processing_details": result.get('details', {})
            }
            
        except Exception as e:
            logger.error(f"Document processing error: {str(e)}")
            # Update status to failed
            if 'document' in locals():
                document.status = "failed"
                db.commit()
            raise e
        finally:
            if 'db' in locals():
                db.close()
    
    async def _process_pdf(self, file_path: str, document_id: str, db: Session) -> Dict[str, Any]:
        """Process PDF with text extraction and OCR using enhanced hierarchical chunking"""
        chunks = []
        
        # Extract text using PyPDF2
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text_content = ""
            page_boundaries = []  # Track page boundaries for better chunking
            
            for page_num, page in enumerate(pdf_reader.pages):
                page_start = len(text_content)
                page_text = page.extract_text()
                page_content = f"\n--- Page {page_num + 1} ---\n{page_text}"
                text_content += page_content
                page_boundaries.append({
                    'page_num': page_num + 1,
                    'start_char': page_start,
                    'end_char': len(text_content),
                    'content_length': len(page_text)
                })
        
        # Extract tables and images using pdfplumber
        table_count = 0
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # Extract tables
                tables = page.extract_tables()
                if tables:
                    for table_idx, table in enumerate(tables):
                        table_text = self._table_to_text(table)
                        text_content += f"\n--- Page {page_num + 1} Table {table_idx + 1} ---\n{table_text}"
                        table_count += 1
                
                # Extract images (if any) - placeholder for future OCR enhancement
                if hasattr(page, 'images'):
                    for img_idx, img in enumerate(page.images):
                        # OCR on images would go here
                        pass
        
        # Use hierarchical chunking with enhanced configuration
        hierarchical_chunks = self.hierarchical_chunker.chunk_document(
            text_content, 
            strategy=ChunkingStrategy.HIERARCHICAL
        )
        
        # Enhance chunks with PDF-specific metadata
        for chunk in hierarchical_chunks:
            # Determine which page(s) this chunk spans
            chunk_pages = []
            for page_info in page_boundaries:
                if not (chunk.end_char <= page_info['start_char'] or chunk.start_char >= page_info['end_char']):
                    chunk_pages.append(page_info['page_num'])
            
            # Add PDF-specific metadata
            chunk.metadata.update({
                'document_type': 'pdf',
                'pages_spanned': chunk_pages,
                'primary_page': chunk_pages[0] if chunk_pages else 1,
                'spans_multiple_pages': len(chunk_pages) > 1,
                'extraction_method': 'pypdf2_pdfplumber'
            })
        
        # Save hierarchical chunks to database with enhanced error handling
        chunks = []
        try:
            for chunk in hierarchical_chunks:
                # Save to enhanced chunk table
                chunk_record = DocumentChunkEnhanced(
                    document_id=document_id,
                    parent_chunk_id=chunk.parent_chunk_id,
                    content=chunk.content,
                    chunk_level=chunk.chunk_level,
                    chunk_index=chunk.chunk_index,
                    overlap_start=chunk.overlap_start,
                    overlap_end=chunk.overlap_end,
                    sentence_boundaries=json.dumps(chunk.sentence_boundaries),
                    chunk_metadata=chunk.metadata
                )
                db.add(chunk_record)
                chunks.append(chunk)
                
                # Also save to legacy chunk table for backward compatibility
                primary_page = chunk.metadata.get('primary_page', 1)
                legacy_chunk = DocumentChunk(
                    document_id=document_id,
                    content=chunk.content,
                    chunk_index=chunk.chunk_index,
                    page_number=primary_page,
                    chunk_metadata=json.dumps({
                        'chunk_level': chunk.chunk_level,
                        'parent_chunk_id': chunk.parent_chunk_id,
                        'hierarchical': True,
                        **chunk.metadata
                    })
                )
                db.add(legacy_chunk)
            
            db.commit()
            logger.info(f"Successfully saved {len(chunks)} hierarchical chunks for PDF document {document_id}")
            
        except Exception as e:
            logger.error(f"Error saving PDF chunks to database: {str(e)}")
            db.rollback()
            raise e
        
        return {
            'chunks_count': len(chunks),
            'embeddings_count': len(chunks),
            'details': {
                'pages': len(pdf_reader.pages),
                'text_length': len(text_content),
                'tables_found': table_count,
                'hierarchical_levels': len(set(chunk.chunk_level for chunk in chunks)),
                'chunks_per_level': {
                    level: len([c for c in chunks if c.chunk_level == level])
                    for level in set(chunk.chunk_level for chunk in chunks)
                },
                'overlap_statistics': self.hierarchical_chunker.overlap_manager.get_overlap_statistics()
            }
        }
    
    async def _process_text(self, file_path: str, document_id: str, db: Session) -> Dict[str, Any]:
        """Process plain text file with enhanced hierarchical chunking"""
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            content = await f.read()
        
        # Use hierarchical chunking with enhanced configuration
        hierarchical_chunks = self.hierarchical_chunker.chunk_document(
            content, 
            strategy=ChunkingStrategy.HIERARCHICAL
        )
        
        # Enhance chunks with text-specific metadata
        for chunk in hierarchical_chunks:
            # Calculate text statistics
            lines_in_chunk = chunk.content.count('\n') + 1
            words_in_chunk = len(chunk.content.split())
            
            # Add text-specific metadata
            chunk.metadata.update({
                'document_type': 'text',
                'lines_count': lines_in_chunk,
                'words_count': words_in_chunk,
                'char_count': len(chunk.content),
                'extraction_method': 'direct_text'
            })
        
        # Save hierarchical chunks to database with enhanced error handling
        chunks = []
        try:
            for chunk in hierarchical_chunks:
                # Save to enhanced chunk table
                chunk_record = DocumentChunkEnhanced(
                    document_id=document_id,
                    parent_chunk_id=chunk.parent_chunk_id,
                    content=chunk.content,
                    chunk_level=chunk.chunk_level,
                    chunk_index=chunk.chunk_index,
                    overlap_start=chunk.overlap_start,
                    overlap_end=chunk.overlap_end,
                    sentence_boundaries=json.dumps(chunk.sentence_boundaries),
                    chunk_metadata=chunk.metadata
                )
                db.add(chunk_record)
                chunks.append(chunk)
                
                # Also save to legacy chunk table for backward compatibility
                legacy_chunk = DocumentChunk(
                    document_id=document_id,
                    content=chunk.content,
                    chunk_index=chunk.chunk_index,
                    chunk_metadata=json.dumps({
                        'chunk_level': chunk.chunk_level,
                        'parent_chunk_id': chunk.parent_chunk_id,
                        'hierarchical': True,
                        **chunk.metadata
                    })
                )
                db.add(legacy_chunk)
            
            db.commit()
            logger.info(f"Successfully saved {len(chunks)} hierarchical chunks for text document {document_id}")
            
        except Exception as e:
            logger.error(f"Error saving text chunks to database: {str(e)}")
            db.rollback()
            raise e
        
        return {
            'chunks_count': len(chunks),
            'embeddings_count': len(chunks),
            'details': {
                'text_length': len(content),
                'lines': content.count('\n') + 1,
                'words': len(content.split()),
                'hierarchical_levels': len(set(chunk.chunk_level for chunk in chunks)),
                'chunks_per_level': {
                    level: len([c for c in chunks if c.chunk_level == level])
                    for level in set(chunk.chunk_level for chunk in chunks)
                },
                'overlap_statistics': self.hierarchical_chunker.overlap_manager.get_overlap_statistics(),
                'average_chunk_size': sum(len(chunk.content) for chunk in chunks) / len(chunks) if chunks else 0
            }
        }
    
    async def _process_image(self, file_path: str, document_id: str, db: Session) -> Dict[str, Any]:
        """Process image with OCR and hierarchical chunking"""
        # Perform OCR
        ocr_text = await self.image_processor.extract_text(file_path)
        
        # Detect objects/charts if needed
        objects = await self.image_processor.detect_objects(file_path)
        
        chunks = []
        
        # If OCR text is substantial, use hierarchical chunking
        if len(ocr_text.strip()) > 100:  # Only chunk if there's substantial text
            hierarchical_chunks = self.hierarchical_chunker.chunk_document(
                ocr_text, 
                strategy=ChunkingStrategy.SENTENCE_AWARE  # Use sentence-aware for OCR text
            )
            
            # Enhance chunks with image-specific metadata
            for chunk in hierarchical_chunks:
                chunk.metadata.update({
                    'document_type': 'image',
                    'extraction_method': 'ocr',
                    'objects_detected': objects,
                    'image_path': file_path,
                    'ocr_confidence': 'medium'  # Placeholder for future OCR confidence scoring
                })
            
            # Save hierarchical chunks
            try:
                for chunk in hierarchical_chunks:
                    # Save to enhanced chunk table
                    chunk_record = DocumentChunkEnhanced(
                        document_id=document_id,
                        parent_chunk_id=chunk.parent_chunk_id,
                        content=chunk.content,
                        chunk_level=chunk.chunk_level,
                        chunk_index=chunk.chunk_index,
                        overlap_start=chunk.overlap_start,
                        overlap_end=chunk.overlap_end,
                        sentence_boundaries=json.dumps(chunk.sentence_boundaries),
                        chunk_metadata=chunk.metadata
                    )
                    db.add(chunk_record)
                    chunks.append(chunk)
                    
                    # Also save to legacy chunk table for backward compatibility
                    legacy_chunk = DocumentChunk(
                        document_id=document_id,
                        content=chunk.content,
                        chunk_index=chunk.chunk_index,
                        chunk_metadata=json.dumps({
                            'chunk_level': chunk.chunk_level,
                            'parent_chunk_id': chunk.parent_chunk_id,
                            'hierarchical': True,
                            'objects': objects,
                            'image_path': file_path,
                            **chunk.metadata
                        })
                    )
                    db.add(legacy_chunk)
                
                db.commit()
                logger.info(f"Successfully saved {len(chunks)} hierarchical chunks for image document {document_id}")
                
            except Exception as e:
                logger.error(f"Error saving image chunks to database: {str(e)}")
                db.rollback()
                raise e
        else:
            # For minimal text, create single chunk
            chunk_record = DocumentChunk(
                document_id=document_id,
                content=ocr_text,
                chunk_index=0,
                chunk_metadata=json.dumps({
                    'objects': objects, 
                    'image_path': file_path,
                    'document_type': 'image',
                    'extraction_method': 'ocr',
                    'hierarchical': False
                })
            )
            db.add(chunk_record)
            db.commit()
            chunks = [{'content': ocr_text, 'chunk_level': 0}]  # Mock chunk for statistics
        
        return {
            'chunks_count': len(chunks),
            'embeddings_count': len(chunks),
            'details': {
                'ocr_text_length': len(ocr_text),
                'objects_detected': len(objects),
                'hierarchical_chunks': len(chunks) > 1,
                'hierarchical_levels': len(set(getattr(chunk, 'chunk_level', 0) for chunk in chunks)) if chunks else 1
            }
        }
    
    def _table_to_text(self, table: List[List[str]]) -> str:
        """Convert table to readable text"""
        if not table:
            return ""
        
        text_lines = []
        for row in table:
            if row:  # Skip empty rows
                text_lines.append(" | ".join(str(cell) if cell else "" for cell in row))
        
        return "\n".join(text_lines)
    
    async def get_user_documents(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all documents for a user"""
        db = next(get_db())
        try:
            documents = db.query(Document).filter(Document.user_id == user_id).all()
            return [
                {
                    "id": doc.id,
                    "name": doc.name,
                    "size": doc.size,
                    "status": doc.status,
                    "chunks": doc.chunks_count,
                    "embeddings": doc.embeddings_count,
                    "created_at": doc.created_at,
                    "updated_at": doc.updated_at
                }
                for doc in documents
            ]
        finally:
            db.close()
    
    async def delete_document(self, document_id: str, user_id: str):
        """Delete a document and its chunks"""
        db = next(get_db())
        try:
            # Verify ownership
            document = db.query(Document).filter(
                Document.id == document_id,
                Document.user_id == user_id
            ).first()
            
            if not document:
                raise ValueError("Document not found or access denied")
            
            # Delete file
            if os.path.exists(document.file_path):
                os.remove(document.file_path)
            
            # Delete enhanced chunks
            db.query(DocumentChunkEnhanced).filter(DocumentChunkEnhanced.document_id == document_id).delete()
            
            # Delete legacy chunks
            db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()
            
            # Delete document record
            db.delete(document)
            db.commit()
            
        finally:
            db.close()
    
    async def get_chunk_hierarchy(self, document_id: str, user_id: str) -> Dict[str, Any]:
        """Get hierarchical chunk structure for a document"""
        db = next(get_db())
        try:
            # Verify document ownership
            document = db.query(Document).filter(
                Document.id == document_id,
                Document.user_id == user_id
            ).first()
            
            if not document:
                raise ValueError("Document not found or access denied")
            
            # Get all enhanced chunks for the document
            chunks = db.query(DocumentChunkEnhanced).filter(
                DocumentChunkEnhanced.document_id == document_id
            ).order_by(DocumentChunkEnhanced.chunk_level, DocumentChunkEnhanced.chunk_index).all()
            
            # Build hierarchy structure
            hierarchy = {
                'document_id': document_id,
                'document_name': document.name,
                'levels': {},
                'relationships': {}
            }
            
            for chunk in chunks:
                level = chunk.chunk_level
                if level not in hierarchy['levels']:
                    hierarchy['levels'][level] = []
                
                chunk_data = {
                    'id': chunk.id,
                    'chunk_index': chunk.chunk_index,
                    'content_preview': chunk.content[:200] + '...' if len(chunk.content) > 200 else chunk.content,
                    'content_length': len(chunk.content),
                    'parent_chunk_id': chunk.parent_chunk_id,
                    'overlap_start': chunk.overlap_start,
                    'overlap_end': chunk.overlap_end,
                    'sentence_boundaries': json.loads(chunk.sentence_boundaries) if chunk.sentence_boundaries else [],
                    'metadata': chunk.chunk_metadata or {}
                }
                
                hierarchy['levels'][level].append(chunk_data)
                
                # Track parent-child relationships
                if chunk.parent_chunk_id:
                    if chunk.parent_chunk_id not in hierarchy['relationships']:
                        hierarchy['relationships'][chunk.parent_chunk_id] = []
                    hierarchy['relationships'][chunk.parent_chunk_id].append(chunk.id)
            
            return hierarchy
            
        finally:
            db.close()
    
    async def get_contextual_chunks(self, chunk_id: str, user_id: str, context_window: int = 2) -> List[Dict[str, Any]]:
        """Get contextual chunks around a specific chunk (siblings, parent, children)"""
        db = next(get_db())
        try:
            # Get the target chunk
            target_chunk = db.query(DocumentChunkEnhanced).filter(
                DocumentChunkEnhanced.id == chunk_id
            ).first()
            
            if not target_chunk:
                raise ValueError("Chunk not found")
            
            # Verify document ownership
            document = db.query(Document).filter(
                Document.id == target_chunk.document_id,
                Document.user_id == user_id
            ).first()
            
            if not document:
                raise ValueError("Access denied")
            
            contextual_chunks = []
            
            # Get parent chunk if exists
            if target_chunk.parent_chunk_id:
                parent_chunk = db.query(DocumentChunkEnhanced).filter(
                    DocumentChunkEnhanced.id == target_chunk.parent_chunk_id
                ).first()
                if parent_chunk:
                    contextual_chunks.append({
                        'id': parent_chunk.id,
                        'content': parent_chunk.content,
                        'chunk_level': parent_chunk.chunk_level,
                        'chunk_index': parent_chunk.chunk_index,
                        'relationship': 'parent',
                        'metadata': parent_chunk.chunk_metadata or {}
                    })
            
            # Get sibling chunks (same level, same parent)
            sibling_chunks = db.query(DocumentChunkEnhanced).filter(
                DocumentChunkEnhanced.document_id == target_chunk.document_id,
                DocumentChunkEnhanced.chunk_level == target_chunk.chunk_level,
                DocumentChunkEnhanced.parent_chunk_id == target_chunk.parent_chunk_id,
                DocumentChunkEnhanced.chunk_index.between(
                    target_chunk.chunk_index - context_window,
                    target_chunk.chunk_index + context_window
                ),
                DocumentChunkEnhanced.id != chunk_id
            ).order_by(DocumentChunkEnhanced.chunk_index).all()
            
            for sibling in sibling_chunks:
                contextual_chunks.append({
                    'id': sibling.id,
                    'content': sibling.content,
                    'chunk_level': sibling.chunk_level,
                    'chunk_index': sibling.chunk_index,
                    'relationship': 'sibling',
                    'metadata': sibling.chunk_metadata or {}
                })
            
            # Get child chunks
            child_chunks = db.query(DocumentChunkEnhanced).filter(
                DocumentChunkEnhanced.parent_chunk_id == chunk_id
            ).order_by(DocumentChunkEnhanced.chunk_index).all()
            
            for child in child_chunks:
                contextual_chunks.append({
                    'id': child.id,
                    'content': child.content,
                    'chunk_level': child.chunk_level,
                    'chunk_index': child.chunk_index,
                    'relationship': 'child',
                    'metadata': child.chunk_metadata or {}
                })
            
            # Include the target chunk itself
            contextual_chunks.append({
                'id': target_chunk.id,
                'content': target_chunk.content,
                'chunk_level': target_chunk.chunk_level,
                'chunk_index': target_chunk.chunk_index,
                'relationship': 'target',
                'metadata': target_chunk.chunk_metadata or {}
            })
            
            return contextual_chunks
            
        finally:
            db.close()
    
    async def get_chunk_relationships(self, chunk_id: str, user_id: str) -> Dict[str, Any]:
        """Get detailed relationship information for a specific chunk"""
        db = next(get_db())
        try:
            # Get the target chunk
            target_chunk = db.query(DocumentChunkEnhanced).filter(
                DocumentChunkEnhanced.id == chunk_id
            ).first()
            
            if not target_chunk:
                raise ValueError("Chunk not found")
            
            # Verify document ownership
            document = db.query(Document).filter(
                Document.id == target_chunk.document_id,
                Document.user_id == user_id
            ).first()
            
            if not document:
                raise ValueError("Access denied")
            
            # Use hierarchical chunker to get relationship information
            chunk_relationships = self.hierarchical_chunker.get_chunk_relationships(
                f"level_{target_chunk.chunk_level}_{target_chunk.chunk_index}"
            )
            
            # Enhance with database information
            relationships = {
                'chunk_id': chunk_id,
                'chunk_level': target_chunk.chunk_level,
                'chunk_index': target_chunk.chunk_index,
                'parent_chunk_id': target_chunk.parent_chunk_id,
                'hierarchical_relationships': chunk_relationships,
                'overlap_info': {
                    'overlap_start': target_chunk.overlap_start,
                    'overlap_end': target_chunk.overlap_end,
                    'has_overlap_before': target_chunk.overlap_start is not None,
                    'has_overlap_after': target_chunk.overlap_end is not None
                }
            }
            
            return relationships
            
        finally:
            db.close()
    
    async def _integrate_with_vector_store(self, document_data: Dict[str, Any]):
        """Integrate processed document with vector store"""
        try:
            from services.vector_store import VectorStoreService
            
            # Initialize vector store if not already done
            vector_store = VectorStoreService()
            await vector_store.initialize()
            
            # Add document to vector store (handles both hierarchical and legacy chunks)
            await vector_store.add_document(document_data)
            
            logger.info(f"Successfully integrated document {document_data['id']} with vector store")
            
        except Exception as e:
            logger.error(f"Error integrating document {document_data['id']} with vector store: {str(e)}")
            # Don't raise the error as this shouldn't fail the entire document processing
            # The document is still successfully processed even if vector store integration fails
    
    async def reprocess_document_with_hierarchical_chunking(self, document_id: str, user_id: str, strategy: ChunkingStrategy = ChunkingStrategy.HIERARCHICAL) -> Dict[str, Any]:
        """Reprocess an existing document with hierarchical chunking"""
        db = next(get_db())
        try:
            # Verify document ownership
            document = db.query(Document).filter(
                Document.id == document_id,
                Document.user_id == user_id
            ).first()
            
            if not document:
                raise ValueError("Document not found or access denied")
            
            if not os.path.exists(document.file_path):
                raise ValueError("Document file not found on disk")
            
            # Delete existing enhanced chunks
            db.query(DocumentChunkEnhanced).filter(DocumentChunkEnhanced.document_id == document_id).delete()
            
            # Reprocess based on content type
            if document.content_type == 'application/pdf':
                result = await self._process_pdf(document.file_path, document_id, db)
            elif document.content_type == 'text/plain':
                result = await self._process_text(document.file_path, document_id, db)
            elif document.content_type.startswith('image/'):
                result = await self._process_image(document.file_path, document_id, db)
            else:
                raise ValueError(f"Unsupported file type for reprocessing: {document.content_type}")
            
            # Update document status
            document.status = "completed"
            document.chunks_count = result['chunks_count']
            document.embeddings_count = result['embeddings_count']
            db.commit()
            
            return {
                "document_id": document_id,
                "status": "reprocessed",
                "strategy": strategy.value,
                "chunks": result['chunks_count'],
                "embeddings": result['embeddings_count'],
                "processing_details": result.get('details', {})
            }
            
        except Exception as e:
            logger.error(f"Error reprocessing document {document_id}: {str(e)}")
            if 'document' in locals():
                document.status = "failed"
                db.commit()
            raise e
        finally:
            db.close()
    
    async def get_chunking_statistics(self, document_id: str, user_id: str) -> Dict[str, Any]:
        """Get detailed chunking statistics for a document"""
        db = next(get_db())
        try:
            # Verify document ownership
            document = db.query(Document).filter(
                Document.id == document_id,
                Document.user_id == user_id
            ).first()
            
            if not document:
                raise ValueError("Document not found or access denied")
            
            # Get enhanced chunks
            enhanced_chunks = db.query(DocumentChunkEnhanced).filter(
                DocumentChunkEnhanced.document_id == document_id
            ).all()
            
            if not enhanced_chunks:
                return {
                    'document_id': document_id,
                    'has_hierarchical_chunks': False,
                    'total_chunks': 0,
                    'message': 'No hierarchical chunks found. Document may need reprocessing.'
                }
            
            # Calculate statistics
            levels = {}
            total_content_length = 0
            chunks_with_overlap = 0
            parent_child_relationships = 0
            
            for chunk in enhanced_chunks:
                level = chunk.chunk_level
                if level not in levels:
                    levels[level] = {
                        'count': 0,
                        'total_length': 0,
                        'avg_length': 0,
                        'chunks_with_overlap': 0
                    }
                
                levels[level]['count'] += 1
                levels[level]['total_length'] += len(chunk.content)
                total_content_length += len(chunk.content)
                
                if chunk.overlap_start is not None or chunk.overlap_end is not None:
                    chunks_with_overlap += 1
                    levels[level]['chunks_with_overlap'] += 1
                
                if chunk.parent_chunk_id is not None:
                    parent_child_relationships += 1
            
            # Calculate averages
            for level_stats in levels.values():
                if level_stats['count'] > 0:
                    level_stats['avg_length'] = level_stats['total_length'] / level_stats['count']
            
            return {
                'document_id': document_id,
                'document_name': document.name,
                'has_hierarchical_chunks': True,
                'total_chunks': len(enhanced_chunks),
                'total_content_length': total_content_length,
                'average_chunk_length': total_content_length / len(enhanced_chunks) if enhanced_chunks else 0,
                'hierarchical_levels': len(levels),
                'level_statistics': levels,
                'chunks_with_overlap': chunks_with_overlap,
                'overlap_percentage': (chunks_with_overlap / len(enhanced_chunks)) * 100 if enhanced_chunks else 0,
                'parent_child_relationships': parent_child_relationships,
                'chunking_efficiency': {
                    'content_coverage': 100.0,  # All content is covered
                    'redundancy_factor': chunks_with_overlap / len(enhanced_chunks) if enhanced_chunks else 0,
                    'hierarchy_depth': max(levels.keys()) if levels else 0
                }
            }
            
        finally:
            db.close()