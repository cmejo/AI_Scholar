"""
Multi-Modal Processing API Endpoints
Provides endpoints for processing various content types including images, audio, video,
documents, and other file formats with advanced extraction capabilities.
"""
import logging
import tempfile
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from core.database import get_db
from core.auth import get_current_user
from models.schemas import User
from services.multimodal_processor import (
    MultiModalProcessor, ProcessingResult, ContentType, 
    ProcessingQuality, ExtractionMethod
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/multimodal", tags=["multimodal"])

# Request/Response Models
class ProcessingRequest(BaseModel):
    quality: ProcessingQuality = ProcessingQuality.BALANCED
    content_type: Optional[ContentType] = None

class BatchProcessingRequest(BaseModel):
    quality: ProcessingQuality = ProcessingQuality.BALANCED
    max_concurrent: int = Field(default=5, ge=1, le=10)

class ProcessingResultResponse(BaseModel):
    content_type: str
    extracted_text: str
    metadata: Dict[str, Any]
    confidence_score: float
    processing_time: float
    extraction_methods: List[str]
    structured_data: Optional[Dict[str, Any]] = None
    thumbnails: Optional[List[str]] = None
    annotations: Optional[List[Dict[str, Any]]] = None

class BatchProcessingResponse(BaseModel):
    results: List[ProcessingResultResponse]
    total_files: int
    successful_files: int
    failed_files: int
    total_processing_time: float

class SupportedFormatsResponse(BaseModel):
    content_types: Dict[str, List[str]]
    processing_qualities: List[str]
    extraction_methods: List[str]

# Endpoints

@router.post("/process", response_model=ProcessingResultResponse)
async def process_single_file(
    file: UploadFile = File(...),
    quality: ProcessingQuality = Form(ProcessingQuality.BALANCED),
    content_type: Optional[ContentType] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process a single uploaded file"""
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as temp_file:
            temp_path = temp_file.name
            content = await file.read()
            temp_file.write(content)
        
        try:
            # Process the file
            processor = MultiModalProcessor(db)
            result = await processor.process_content(
                file_path=temp_path,
                content_type=content_type,
                quality=quality,
                user_id=current_user.id
            )
            
            return ProcessingResultResponse(
                content_type=result.content_type.value,
                extracted_text=result.extracted_text,
                metadata=result.metadata,
                confidence_score=result.confidence_score,
                processing_time=result.processing_time,
                extraction_methods=[method.value for method in result.extraction_methods],
                structured_data=result.structured_data,
                thumbnails=result.thumbnails,
                annotations=result.annotations
            )
            
        finally:
            # Clean up temporary file
            os.unlink(temp_path)
            
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process-batch", response_model=BatchProcessingResponse)
async def process_multiple_files(
    files: List[UploadFile] = File(...),
    quality: ProcessingQuality = Form(ProcessingQuality.BALANCED),
    max_concurrent: int = Form(5),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process multiple uploaded files concurrently"""
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        if len(files) > 20:  # Limit batch size
            raise HTTPException(status_code=400, detail="Too many files. Maximum 20 files per batch.")
        
        start_time = datetime.utcnow()
        temp_paths = []
        
        # Save all files to temporary locations
        for file in files:
            if not file.filename:
                continue
                
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}")
            temp_path = temp_file.name
            content = await file.read()
            temp_file.write(content)
            temp_file.close()
            temp_paths.append(temp_path)
        
        try:
            # Process files in batch
            processor = MultiModalProcessor(db)
            results = await processor.process_content_batch(
                file_paths=temp_paths,
                quality=quality,
                user_id=current_user.id,
                max_concurrent=max_concurrent
            )
            
            # Convert results to response format
            response_results = []
            for result in results:
                response_results.append(ProcessingResultResponse(
                    content_type=result.content_type.value,
                    extracted_text=result.extracted_text,
                    metadata=result.metadata,
                    confidence_score=result.confidence_score,
                    processing_time=result.processing_time,
                    extraction_methods=[method.value for method in result.extraction_methods],
                    structured_data=result.structured_data,
                    thumbnails=result.thumbnails,
                    annotations=result.annotations
                ))
            
            total_processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return BatchProcessingResponse(
                results=response_results,
                total_files=len(files),
                successful_files=len(results),
                failed_files=len(files) - len(results),
                total_processing_time=total_processing_time
            )
            
        finally:
            # Clean up temporary files
            for temp_path in temp_paths:
                try:
                    os.unlink(temp_path)
                except:
                    pass
                    
    except Exception as e:
        logger.error(f"Error processing batch: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-image", response_model=ProcessingResultResponse)
async def analyze_image(
    image: UploadFile = File(...),
    quality: ProcessingQuality = Form(ProcessingQuality.BALANCED),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Specialized endpoint for image analysis with detailed results"""
    try:
        # Validate image file
        if not image.content_type or not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{image.filename}") as temp_file:
            temp_path = temp_file.name
            content = await image.read()
            temp_file.write(content)
        
        try:
            # Process the image
            processor = MultiModalProcessor(db)
            result = await processor.process_content(
                file_path=temp_path,
                content_type=ContentType.IMAGE,
                quality=quality,
                user_id=current_user.id
            )
            
            return ProcessingResultResponse(
                content_type=result.content_type.value,
                extracted_text=result.extracted_text,
                metadata=result.metadata,
                confidence_score=result.confidence_score,
                processing_time=result.processing_time,
                extraction_methods=[method.value for method in result.extraction_methods],
                structured_data=result.structured_data,
                thumbnails=result.thumbnails,
                annotations=result.annotations
            )
            
        finally:
            os.unlink(temp_path)
            
    except Exception as e:
        logger.error(f"Error analyzing image: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/transcribe-audio", response_model=ProcessingResultResponse)
async def transcribe_audio(
    audio: UploadFile = File(...),
    quality: ProcessingQuality = Form(ProcessingQuality.BALANCED),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Specialized endpoint for audio transcription"""
    try:
        # Validate audio file
        if not audio.content_type or not audio.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="File must be an audio file")
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{audio.filename}") as temp_file:
            temp_path = temp_file.name
            content = await audio.read()
            temp_file.write(content)
        
        try:
            # Process the audio
            processor = MultiModalProcessor(db)
            result = await processor.process_content(
                file_path=temp_path,
                content_type=ContentType.AUDIO,
                quality=quality,
                user_id=current_user.id
            )
            
            return ProcessingResultResponse(
                content_type=result.content_type.value,
                extracted_text=result.extracted_text,
                metadata=result.metadata,
                confidence_score=result.confidence_score,
                processing_time=result.processing_time,
                extraction_methods=[method.value for method in result.extraction_methods],
                structured_data=result.structured_data,
                thumbnails=result.thumbnails,
                annotations=result.annotations
            )
            
        finally:
            os.unlink(temp_path)
            
    except Exception as e:
        logger.error(f"Error transcribing audio: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-video", response_model=ProcessingResultResponse)
async def analyze_video(
    video: UploadFile = File(...),
    quality: ProcessingQuality = Form(ProcessingQuality.BALANCED),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Specialized endpoint for video analysis"""
    try:
        # Validate video file
        if not video.content_type or not video.content_type.startswith('video/'):
            raise HTTPException(status_code=400, detail="File must be a video file")
        
        # Check file size (limit to 100MB for video processing)
        max_size = 100 * 1024 * 1024  # 100MB
        content = await video.read()
        if len(content) > max_size:
            raise HTTPException(status_code=400, detail="Video file too large. Maximum size is 100MB.")
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{video.filename}") as temp_file:
            temp_path = temp_file.name
            temp_file.write(content)
        
        try:
            # Process the video
            processor = MultiModalProcessor(db)
            result = await processor.process_content(
                file_path=temp_path,
                content_type=ContentType.VIDEO,
                quality=quality,
                user_id=current_user.id
            )
            
            return ProcessingResultResponse(
                content_type=result.content_type.value,
                extracted_text=result.extracted_text,
                metadata=result.metadata,
                confidence_score=result.confidence_score,
                processing_time=result.processing_time,
                extraction_methods=[method.value for method in result.extraction_methods],
                structured_data=result.structured_data,
                thumbnails=result.thumbnails,
                annotations=result.annotations
            )
            
        finally:
            os.unlink(temp_path)
            
    except Exception as e:
        logger.error(f"Error analyzing video: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/extract-document", response_model=ProcessingResultResponse)
async def extract_document_content(
    document: UploadFile = File(...),
    quality: ProcessingQuality = Form(ProcessingQuality.BALANCED),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Extract content from document files (PDF, DOCX, etc.)"""
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{document.filename}") as temp_file:
            temp_path = temp_file.name
            content = await document.read()
            temp_file.write(content)
        
        try:
            # Process the document
            processor = MultiModalProcessor(db)
            result = await processor.process_content(
                file_path=temp_path,
                quality=quality,
                user_id=current_user.id
            )
            
            return ProcessingResultResponse(
                content_type=result.content_type.value,
                extracted_text=result.extracted_text,
                metadata=result.metadata,
                confidence_score=result.confidence_score,
                processing_time=result.processing_time,
                extraction_methods=[method.value for method in result.extraction_methods],
                structured_data=result.structured_data,
                thumbnails=result.thumbnails,
                annotations=result.annotations
            )
            
        finally:
            os.unlink(temp_path)
            
    except Exception as e:
        logger.error(f"Error extracting document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/supported-formats", response_model=SupportedFormatsResponse)
async def get_supported_formats():
    """Get list of supported file formats and processing options"""
    try:
        processor = MultiModalProcessor(None)  # No DB needed for this
        
        # Convert supported extensions to response format
        content_types = {}
        for content_type, extensions in processor.supported_extensions.items():
            content_types[content_type.value] = extensions
        
        processing_qualities = [quality.value for quality in ProcessingQuality]
        extraction_methods = [method.value for method in ExtractionMethod]
        
        return SupportedFormatsResponse(
            content_types=content_types,
            processing_qualities=processing_qualities,
            extraction_methods=extraction_methods
        )
        
    except Exception as e:
        logger.error(f"Error getting supported formats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/processing-stats", response_model=Dict[str, Any])
async def get_processing_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = Query(default=30, ge=1, le=365)
):
    """Get user's processing statistics"""
    try:
        from core.database import AnalyticsEvent
        from datetime import timedelta
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Query processing events
        events = db.query(AnalyticsEvent).filter(
            AnalyticsEvent.user_id == current_user.id,
            AnalyticsEvent.event_type == "multimodal_processing",
            AnalyticsEvent.created_at >= start_date,
            AnalyticsEvent.created_at <= end_date
        ).all()
        
        # Analyze statistics
        stats = {
            "total_files_processed": len(events),
            "content_type_breakdown": {},
            "quality_breakdown": {},
            "average_processing_time": 0.0,
            "total_processing_time": 0.0,
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days
            }
        }
        
        if events:
            # Content type breakdown
            content_types = {}
            qualities = {}
            processing_times = []
            
            for event in events:
                event_data = event.event_data
                
                content_type = event_data.get("content_type", "unknown")
                content_types[content_type] = content_types.get(content_type, 0) + 1
                
                quality = event_data.get("quality", "unknown")
                qualities[quality] = qualities.get(quality, 0) + 1
                
                processing_time = event_data.get("processing_time", 0.0)
                processing_times.append(processing_time)
            
            stats["content_type_breakdown"] = content_types
            stats["quality_breakdown"] = qualities
            stats["average_processing_time"] = sum(processing_times) / len(processing_times)
            stats["total_processing_time"] = sum(processing_times)
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting processing statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/content-types", response_model=List[Dict[str, str]])
async def get_content_types():
    """Get list of available content types"""
    try:
        content_types = []
        for content_type in ContentType:
            content_types.append({
                "value": content_type.value,
                "name": content_type.value.replace("_", " ").title(),
                "description": f"{content_type.value.replace('_', ' ').title()} content processing"
            })
        
        return content_types
        
    except Exception as e:
        logger.error(f"Error getting content types: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/processing-qualities", response_model=List[Dict[str, str]])
async def get_processing_qualities():
    """Get list of available processing quality levels"""
    try:
        qualities = []
        quality_descriptions = {
            ProcessingQuality.FAST: "Fast processing with basic quality",
            ProcessingQuality.BALANCED: "Balanced processing speed and quality",
            ProcessingQuality.HIGH_QUALITY: "High quality processing with longer processing time",
            ProcessingQuality.MAXIMUM: "Maximum quality processing with longest processing time"
        }
        
        for quality in ProcessingQuality:
            qualities.append({
                "value": quality.value,
                "name": quality.value.replace("_", " ").title(),
                "description": quality_descriptions.get(quality, "Processing quality level")
            })
        
        return qualities
        
    except Exception as e:
        logger.error(f"Error getting processing qualities: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check for multimodal processing service"""
    try:
        # Basic health check - could be expanded to check model availability
        return {
            "status": "healthy",
            "service": "multimodal_processor",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Service unhealthy")