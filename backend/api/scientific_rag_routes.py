"""
Scientific RAG API Routes for AI Scholar
Provides endpoints for document processing, querying, and corpus management
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import logging
import asyncio
from pathlib import Path
import tempfile
import os

from ..services.scientific_rag_service import scientific_rag_service
from ..services.ollama_service import ollama_service
from ..services.vector_store_service import vector_store_service
from ..auth.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rag", tags=["Scientific RAG"])

# Pydantic models for request/response
class ScientificQuery(BaseModel):
    query: str = Field(..., description="Scientific research question")
    model: Optional[str] = Field("llama2", description="LLM model to use")
    max_sources: Optional[int] = Field(10, description="Maximum number of sources to use")
    filters: Optional[Dict[str, Any]] = Field(None, description="Search filters")

class QueryResponse(BaseModel):
    query: str
    query_type: str
    response: str
    sources: List[Dict[str, Any]]
    context_chunks_used: int
    total_results_found: int
    confidence_score: float
    processing_time: float
    model_used: str
    timestamp: str

class BulkUploadRequest(BaseModel):
    process_immediately: Optional[bool] = Field(True, description="Process files immediately")
    notification_email: Optional[str] = Field(None, description="Email for completion notification")

class CorpusStats(BaseModel):
    total_documents: int
    total_chunks: int
    total_embeddings: int
    average_document_length: float
    most_common_sections: List[str]
    processing_quality_distribution: Dict[str, int]
    last_updated: str

# Global variables for tracking upload progress
upload_progress = {}

@router.post("/query", response_model=QueryResponse)
async def scientific_query(
    query_request: ScientificQuery,
    current_user = Depends(get_current_user)
):
    """
    Process a scientific research query using RAG pipeline
    
    This endpoint:
    1. Analyzes the scientific query
    2. Retrieves relevant document chunks
    3. Generates a response using Ollama LLM
    4. Returns the response with source citations
    """
    try:
        logger.info(f"Processing scientific query from user {current_user.get('email', 'unknown')}: {query_request.query[:100]}...")
        
        result = await scientific_rag_service.process_scientific_query(
            query=query_request.query,
            filters=query_request.filters,
            model=query_request.model,
            max_sources=query_request.max_sources
        )
        
        if result.get('error'):
            raise HTTPException(status_code=500, detail=result.get('response', 'Unknown error'))
        
        return QueryResponse(**result)
        
    except Exception as e:
        logger.error(f"Error processing scientific query: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process query: {str(e)}")

@router.post("/upload-pdf")
async def upload_single_pdf(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user = Depends(get_current_user)
):
    """
    Upload and process a single PDF document
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Process PDF in background
        background_tasks.add_task(
            process_single_pdf_background,
            temp_file_path,
            file.filename,
            current_user.get('id')
        )
        
        return {
            "message": "PDF uploaded successfully and is being processed",
            "filename": file.filename,
            "size_bytes": len(content),
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Error uploading PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload PDF: {str(e)}")

@router.post("/bulk-upload")
async def bulk_upload_pdfs(
    files: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user = Depends(get_current_user)
):
    """
    Upload and process multiple PDF documents
    """
    # Validate files
    pdf_files = []
    for file in files:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400, 
                detail=f"File {file.filename} is not a PDF. Only PDF files are supported."
            )
        pdf_files.append(file)
    
    if len(pdf_files) > 100:  # Limit bulk uploads
        raise HTTPException(
            status_code=400, 
            detail="Maximum 100 files allowed per bulk upload"
        )
    
    try:
        # Generate upload session ID
        upload_id = f"upload_{current_user.get('id', 'unknown')}_{len(upload_progress)}"
        
        # Initialize progress tracking
        upload_progress[upload_id] = {
            'total_files': len(pdf_files),
            'processed_files': 0,
            'failed_files': 0,
            'current_file': '',
            'status': 'starting',
            'start_time': None,
            'estimated_completion': None
        }
        
        # Save files temporarily
        temp_file_paths = []
        file_names = []
        
        for file in pdf_files:
            content = await file.read()
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                temp_file.write(content)
                temp_file_paths.append(temp_file.name)
                file_names.append(file.filename)
        
        # Process files in background
        background_tasks.add_task(
            process_bulk_pdfs_background,
            temp_file_paths,
            file_names,
            upload_id,
            current_user.get('id')
        )
        
        return {
            "message": f"Bulk upload started for {len(pdf_files)} files",
            "upload_id": upload_id,
            "total_files": len(pdf_files),
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Error in bulk upload: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start bulk upload: {str(e)}")

@router.get("/upload-progress/{upload_id}")
async def get_upload_progress(
    upload_id: str,
    current_user = Depends(get_current_user)
):
    """
    Get progress of bulk upload operation
    """
    if upload_id not in upload_progress:
        raise HTTPException(status_code=404, detail="Upload session not found")
    
    progress = upload_progress[upload_id]
    
    # Calculate progress percentage
    if progress['total_files'] > 0:
        progress_percent = (progress['processed_files'] / progress['total_files']) * 100
    else:
        progress_percent = 0
    
    return {
        "upload_id": upload_id,
        "progress_percent": progress_percent,
        "processed_files": progress['processed_files'],
        "failed_files": progress['failed_files'],
        "total_files": progress['total_files'],
        "current_file": progress['current_file'],
        "status": progress['status']
    }

@router.get("/corpus/stats", response_model=CorpusStats)
async def get_corpus_statistics(
    current_user = Depends(get_current_user)
):
    """
    Get statistics about the scientific document corpus
    """
    try:
        stats = await scientific_rag_service.get_corpus_statistics()
        return CorpusStats(**stats)
        
    except Exception as e:
        logger.error(f"Error getting corpus statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get corpus statistics: {str(e)}")

@router.get("/models")
async def get_available_models(
    current_user = Depends(get_current_user)
):
    """
    Get list of available Ollama models for scientific queries
    """
    try:
        models = ollama_service.get_available_models()
        return {
            "available_models": models,
            "current_model": ollama_service.current_model,
            "recommended_models": {
                "general": "llama2",
                "fast": "mistral",
                "technical": "codellama",
                "large": "llama2:13b"
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting available models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get models: {str(e)}")

@router.post("/models/{model_name}/set")
async def set_active_model(
    model_name: str,
    current_user = Depends(get_current_user)
):
    """
    Set the active model for scientific queries
    """
    try:
        success = await ollama_service.set_model(model_name)
        if success:
            return {"message": f"Model set to {model_name}", "active_model": model_name}
        else:
            raise HTTPException(status_code=400, detail=f"Failed to set model to {model_name}")
            
    except Exception as e:
        logger.error(f"Error setting model: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to set model: {str(e)}")

@router.post("/process-arxiv-dataset")
async def process_arxiv_dataset(
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """
    Process the entire arXiv dataset located at /home/cmejo/arxiv-dataset/pdf
    """
    arxiv_path = Path("/home/cmejo/arxiv-dataset/pdf")
    
    if not arxiv_path.exists():
        raise HTTPException(
            status_code=404, 
            detail=f"arXiv dataset not found at {arxiv_path}"
        )
    
    # Count PDF files
    pdf_files = list(arxiv_path.glob("*.pdf"))
    if not pdf_files:
        raise HTTPException(
            status_code=404, 
            detail="No PDF files found in arXiv dataset directory"
        )
    
    # Generate processing session ID
    session_id = f"arxiv_processing_{current_user.get('id', 'unknown')}"
    
    # Initialize progress tracking
    upload_progress[session_id] = {
        'total_files': len(pdf_files),
        'processed_files': 0,
        'failed_files': 0,
        'current_file': '',
        'status': 'starting',
        'start_time': None,
        'estimated_completion': None
    }
    
    # Start processing in background
    background_tasks.add_task(
        process_arxiv_dataset_background,
        [str(f) for f in pdf_files],
        session_id,
        current_user.get('id')
    )
    
    return {
        "message": f"Started processing {len(pdf_files)} PDFs from arXiv dataset",
        "session_id": session_id,
        "total_files": len(pdf_files),
        "dataset_path": str(arxiv_path),
        "status": "processing"
    }

@router.get("/search-papers")
async def search_similar_papers(
    query: str,
    limit: int = 20,
    current_user = Depends(get_current_user)
):
    """
    Search for papers similar to the given query
    """
    try:
        papers = await scientific_rag_service.search_similar_papers(query, limit)
        return {
            "query": query,
            "papers": papers,
            "total_found": len(papers)
        }
        
    except Exception as e:
        logger.error(f"Error searching papers: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search papers: {str(e)}")

@router.get("/health")
async def health_check():
    """
    Check the health of RAG system components
    """
    try:
        # Check vector store
        vector_health = await vector_store_service.health_check()
        
        # Check Ollama service
        ollama_health = await ollama_service.health_check()
        
        overall_status = "healthy"
        if vector_health.get('status') != 'healthy' or ollama_health.get('status') != 'healthy':
            overall_status = "degraded"
        
        return {
            "status": overall_status,
            "components": {
                "vector_store": vector_health,
                "ollama": ollama_health
            },
            "timestamp": vector_health.get('last_check')
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": None
        }

# Background task functions
async def process_single_pdf_background(
    pdf_path: str, 
    filename: str, 
    user_id: str
):
    """Background task to process a single PDF"""
    try:
        logger.info(f"Processing PDF: {filename}")
        
        # Extract content from PDF
        document_data = scientific_rag_service.pdf_processor.extract_comprehensive_content(pdf_path)
        
        # Create chunks for vector storage
        chunks = scientific_rag_service._create_scientific_chunks(document_data)
        
        # Add to vector store
        await vector_store_service.add_document_chunks(
            document_data['document_id'],
            chunks
        )
        
        logger.info(f"Successfully processed PDF: {filename} ({len(chunks)} chunks)")
        
    except Exception as e:
        logger.error(f"Failed to process PDF {filename}: {e}")
    finally:
        # Clean up temporary file
        try:
            os.unlink(pdf_path)
        except:
            pass

async def process_bulk_pdfs_background(
    pdf_paths: List[str], 
    filenames: List[str], 
    upload_id: str, 
    user_id: str
):
    """Background task to process multiple PDFs"""
    from datetime import datetime
    
    progress = upload_progress[upload_id]
    progress['status'] = 'processing'
    progress['start_time'] = datetime.now().isoformat()
    
    for i, (pdf_path, filename) in enumerate(zip(pdf_paths, filenames)):
        try:
            progress['current_file'] = filename
            
            # Process PDF
            document_data = scientific_rag_service.pdf_processor.extract_comprehensive_content(pdf_path)
            chunks = scientific_rag_service._create_scientific_chunks(document_data)
            
            # Add to vector store
            await vector_store_service.add_document_chunks(
                document_data['document_id'],
                chunks
            )
            
            progress['processed_files'] += 1
            logger.info(f"Processed {filename} ({i+1}/{len(pdf_paths)})")
            
        except Exception as e:
            progress['failed_files'] += 1
            logger.error(f"Failed to process {filename}: {e}")
        finally:
            # Clean up temporary file
            try:
                os.unlink(pdf_path)
            except:
                pass
    
    progress['status'] = 'completed'
    progress['current_file'] = ''

async def process_arxiv_dataset_background(
    pdf_paths: List[str], 
    session_id: str, 
    user_id: str
):
    """Background task to process the entire arXiv dataset"""
    from datetime import datetime
    
    progress = upload_progress[session_id]
    progress['status'] = 'processing'
    progress['start_time'] = datetime.now().isoformat()
    
    for i, pdf_path in enumerate(pdf_paths):
        try:
            filename = Path(pdf_path).name
            progress['current_file'] = filename
            
            # Process PDF
            document_data = scientific_rag_service.pdf_processor.extract_comprehensive_content(pdf_path)
            chunks = scientific_rag_service._create_scientific_chunks(document_data)
            
            # Add to vector store
            await vector_store_service.add_document_chunks(
                document_data['document_id'],
                chunks
            )
            
            progress['processed_files'] += 1
            
            # Log progress every 10 files
            if (i + 1) % 10 == 0:
                logger.info(f"Processed {i+1}/{len(pdf_paths)} arXiv papers")
            
        except Exception as e:
            progress['failed_files'] += 1
            logger.error(f"Failed to process {Path(pdf_path).name}: {e}")
    
    progress['status'] = 'completed'
    progress['current_file'] = ''
    logger.info(f"Completed processing arXiv dataset: {progress['processed_files']} successful, {progress['failed_files']} failed")