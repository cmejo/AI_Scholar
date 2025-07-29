"""
Custom AI Model Training API Endpoints
Provides endpoints for creating, managing, and deploying custom AI models.
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Body, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from core.database import get_db
from core.auth import get_current_user
from models.schemas import User
from services.custom_ai_training import (
    CustomAITrainingService, TrainingJob, CustomModel,
    ModelType, TrainingStatus
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai-training", tags=["ai-training"])

# Request/Response Models
class CreateTrainingJobRequest(BaseModel):
    model_type: ModelType
    model_name: str
    base_model: str
    training_data: Dict[str, Any]
    hyperparameters: Optional[Dict[str, Any]] = None

class TrainingJobResponse(BaseModel):
    id: str
    model_type: str
    model_name: str
    base_model: str
    status: str
    progress: float
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    metrics: Dict[str, float]
    error_message: Optional[str]

class CustomModelResponse(BaseModel):
    id: str
    name: str
    model_type: str
    base_model: str
    performance_metrics: Dict[str, float]
    created_at: str
    is_active: bool
    usage_count: int
    last_used: Optional[str]

class ModelInferenceRequest(BaseModel):
    model_id: str
    input_data: Any

# Endpoints

@router.post("/jobs/create", response_model=TrainingJobResponse)
async def create_training_job(
    request: CreateTrainingJobRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new model training job"""
    try:
        training_service = CustomAITrainingService(db)
        
        job = await training_service.create_training_job(
            user_id=current_user.id,
            model_type=request.model_type,
            model_name=request.model_name,
            base_model=request.base_model,
            training_data=request.training_data,
            hyperparameters=request.hyperparameters
        )
        
        return TrainingJobResponse(
            id=job.id,
            model_type=job.model_type.value,
            model_name=job.model_name,
            base_model=job.base_model,
            status=job.status.value,
            progress=job.progress,
            created_at=job.created_at.isoformat(),
            started_at=job.started_at.isoformat() if job.started_at else None,
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
            metrics=job.metrics,
            error_message=job.error_message
        )
        
    except Exception as e:
        logger.error(f"Error creating training job: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs/{job_id}", response_model=TrainingJobResponse)
async def get_training_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get status of a training job"""
    try:
        training_service = CustomAITrainingService(db)
        
        job = await training_service.get_training_job_status(
            user_id=current_user.id,
            job_id=job_id
        )
        
        return TrainingJobResponse(
            id=job.id,
            model_type=job.model_type.value,
            model_name=job.model_name,
            base_model=job.base_model,
            status=job.status.value,
            progress=job.progress,
            created_at=job.created_at.isoformat(),
            started_at=job.started_at.isoformat() if job.started_at else None,
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
            metrics=job.metrics,
            error_message=job.error_message
        )
        
    except Exception as e:
        logger.error(f"Error getting training job status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/jobs/{job_id}/cancel")
async def cancel_training_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel a training job"""
    try:
        training_service = CustomAITrainingService(db)
        
        success = await training_service.cancel_training_job(
            user_id=current_user.id,
            job_id=job_id
        )
        
        if success:
            return {"message": "Training job cancelled successfully"}
        else:
            raise HTTPException(status_code=400, detail="Cannot cancel job")
        
    except Exception as e:
        logger.error(f"Error cancelling training job: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/models/deploy", response_model=CustomModelResponse)
async def deploy_trained_model(
    job_id: str = Body(...),
    model_name: str = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deploy a trained model for use"""
    try:
        training_service = CustomAITrainingService(db)
        
        model = await training_service.deploy_trained_model(
            user_id=current_user.id,
            job_id=job_id,
            model_name=model_name
        )
        
        return CustomModelResponse(
            id=model.id,
            name=model.name,
            model_type=model.model_type.value,
            base_model=model.base_model,
            performance_metrics=model.performance_metrics,
            created_at=model.created_at.isoformat(),
            is_active=model.is_active,
            usage_count=model.usage_count,
            last_used=model.last_used.isoformat() if model.last_used else None
        )
        
    except Exception as e:
        logger.error(f"Error deploying trained model: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/models/inference", response_model=Dict[str, Any])
async def use_custom_model(
    request: ModelInferenceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Use a deployed custom model for inference"""
    try:
        training_service = CustomAITrainingService(db)
        
        result = await training_service.use_custom_model(
            user_id=current_user.id,
            model_id=request.model_id,
            input_data=request.input_data
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error using custom model: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models", response_model=List[CustomModelResponse])
async def get_user_models(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's deployed models"""
    try:
        training_service = CustomAITrainingService(db)
        
        # Get models for user
        user_models = []
        for model in training_service.trained_models.values():
            if model.user_id == current_user.id:
                user_models.append(CustomModelResponse(
                    id=model.id,
                    name=model.name,
                    model_type=model.model_type.value,
                    base_model=model.base_model,
                    performance_metrics=model.performance_metrics,
                    created_at=model.created_at.isoformat(),
                    is_active=model.is_active,
                    usage_count=model.usage_count,
                    last_used=model.last_used.isoformat() if model.last_used else None
                ))
        
        return user_models
        
    except Exception as e:
        logger.error(f"Error getting user models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/model-types", response_model=List[Dict[str, str]])
async def get_model_types():
    """Get available model types for training"""
    try:
        types = []
        
        type_descriptions = {
            ModelType.TEXT_CLASSIFIER: "Text classification models for categorizing documents",
            ModelType.EMBEDDING_MODEL: "Embedding models for semantic similarity",
            ModelType.QUESTION_ANSWERING: "Question answering models",
            ModelType.SUMMARIZATION: "Text summarization models",
            ModelType.NAMED_ENTITY_RECOGNITION: "Named entity recognition models",
            ModelType.SENTIMENT_ANALYSIS: "Sentiment analysis models"
        }
        
        for model_type in ModelType:
            types.append({
                "value": model_type.value,
                "name": model_type.value.replace("_", " ").title(),
                "description": type_descriptions.get(model_type, "AI model type")
            })
        
        return types
        
    except Exception as e:
        logger.error(f"Error getting model types: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/base-models/{model_type}", response_model=List[str])
async def get_base_models(
    model_type: ModelType,
    db: Session = Depends(get_db)
):
    """Get available base models for a model type"""
    try:
        training_service = CustomAITrainingService(db)
        
        base_models = training_service.model_configs.get(model_type, {}).get("base_models", [])
        
        return base_models
        
    except Exception as e:
        logger.error(f"Error getting base models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check for AI training service"""
    try:
        return {
            "status": "healthy",
            "service": "custom_ai_training",
            "timestamp": datetime.utcnow().isoformat(),
            "features": [
                "model_training",
                "model_deployment",
                "custom_inference",
                "training_monitoring"
            ]
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Service unhealthy")