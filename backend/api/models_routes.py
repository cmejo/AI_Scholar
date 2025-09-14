"""
Models API Routes for AI Scholar
Handles model selection, information, and management
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
import logging
from ..services.ollama_service import OllamaService
from ..core.service_manager import ServiceManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/models", tags=["models"])

def get_ollama_service() -> OllamaService:
    """Get Ollama service instance"""
    service_manager = ServiceManager()
    return service_manager.get_service("ollama")

@router.get("/available", response_model=List[Dict[str, Any]])
async def get_available_models(ollama_service: OllamaService = Depends(get_ollama_service)):
    """Get list of available models with detailed information"""
    try:
        await ollama_service.list_models()
        
        models_info = []
        for model_name in ollama_service.scientific_models.keys():
            model_info = ollama_service.get_model_info(model_name)
            models_info.append(model_info)
        
        # Sort by availability and performance
        models_info.sort(key=lambda x: (not x["available"], x["name"]))
        
        return models_info
    except Exception as e:
        logger.error(f"Error getting available models: {e}")
        raise HTTPException(status_code=500, detail="Failed to get available models")

@router.get("/current")
async def get_current_model(ollama_service: OllamaService = Depends(get_ollama_service)):
    """Get currently selected model"""
    try:
        current_model = ollama_service.current_model
        model_info = ollama_service.get_model_info(current_model)
        return {
            "current_model": current_model,
            "model_info": model_info,
            "available_models": len(ollama_service.available_models)
        }
    except Exception as e:
        logger.error(f"Error getting current model: {e}")
        raise HTTPException(status_code=500, detail="Failed to get current model")

@router.post("/select/{model_name}")
async def select_model(
    model_name: str, 
    ollama_service: OllamaService = Depends(get_ollama_service)
):
    """Select a model for use"""
    try:
        # Check if model is available
        if not any(model_name in available for available in ollama_service.available_models):
            # Try to pull the model
            logger.info(f"Model {model_name} not available, attempting to pull...")
            success = await ollama_service.pull_model(model_name)
            if not success:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Model {model_name} not available and could not be pulled"
                )
        
        # Set as current model
        ollama_service.current_model = model_name
        model_info = ollama_service.get_model_info(model_name)
        
        logger.info(f"Model switched to {model_name}")
        return {
            "message": f"Successfully switched to model {model_name}",
            "current_model": model_name,
            "model_info": model_info
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error selecting model {model_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to select model {model_name}")

@router.get("/recommend/{query_type}")
async def get_model_recommendation(
    query_type: str,
    ollama_service: OllamaService = Depends(get_ollama_service)
):
    """Get model recommendation based on query type"""
    try:
        recommended_model = ollama_service.get_recommended_model(query_type)
        model_info = ollama_service.get_model_info(recommended_model)
        
        return {
            "query_type": query_type,
            "recommended_model": recommended_model,
            "model_info": model_info,
            "alternatives": [
                ollama_service.get_model_info(model) 
                for model in ollama_service.scientific_models.keys()
                if ollama_service.get_model_info(model)["available"] and model != recommended_model
            ][:3]  # Top 3 alternatives
        }
    except Exception as e:
        logger.error(f"Error getting model recommendation for {query_type}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get model recommendation")

@router.post("/pull/{model_name}")
async def pull_model(
    model_name: str,
    ollama_service: OllamaService = Depends(get_ollama_service)
):
    """Pull a model from the registry"""
    try:
        if model_name not in ollama_service.scientific_models:
            raise HTTPException(status_code=400, detail=f"Model {model_name} not supported")
        
        logger.info(f"Starting pull for model {model_name}")
        success = await ollama_service.pull_model(model_name)
        
        if success:
            model_info = ollama_service.get_model_info(model_name)
            return {
                "message": f"Successfully pulled model {model_name}",
                "model_name": model_name,
                "model_info": model_info
            }
        else:
            raise HTTPException(status_code=500, detail=f"Failed to pull model {model_name}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pulling model {model_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to pull model {model_name}")

@router.get("/performance")
async def get_model_performance(ollama_service: OllamaService = Depends(get_ollama_service)):
    """Get performance comparison of available models"""
    try:
        performance_data = []
        
        for model_name in ollama_service.scientific_models.keys():
            model_info = ollama_service.get_model_info(model_name)
            if model_info["available"]:
                performance_data.append({
                    "model": model_name,
                    "description": model_info["description"],
                    "type": model_info["type"],
                    "size": model_info["size"],
                    "performance": model_info["performance"]
                })
        
        return {
            "available_models": len(performance_data),
            "performance_data": performance_data,
            "recommendations": {
                "fastest": ollama_service.get_recommended_model("fast"),
                "best_quality": ollama_service.get_recommended_model("complex"),
                "balanced": ollama_service.get_recommended_model("general"),
                "technical": ollama_service.get_recommended_model("technical")
            }
        }
    except Exception as e:
        logger.error(f"Error getting model performance data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get model performance data")

@router.get("/health")
async def check_models_health(ollama_service: OllamaService = Depends(get_ollama_service)):
    """Check health of model service"""
    try:
        health_status = await ollama_service.check_health()
        available_models = await ollama_service.list_models()
        
        return {
            "service_healthy": health_status,
            "available_models_count": len(available_models),
            "current_model": ollama_service.current_model,
            "supported_models_count": len(ollama_service.scientific_models),
            "timestamp": "2024-12-19T10:00:00Z"
        }
    except Exception as e:
        logger.error(f"Error checking models health: {e}")
        raise HTTPException(status_code=500, detail="Failed to check models health")