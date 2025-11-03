"""
Simplified FastAPI application for chat functionality
"""
import logging
import json
from datetime import datetime, timezone
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Scholar Chat API",
    description="Simplified AI Scholar Chat with Ollama Integration",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple Ollama service class
class SimpleOllamaService:
    def __init__(self, base_url: str = None):
        # Use environment variable or default to localhost
        import os
        self.base_url = base_url or os.getenv('OLLAMA_HOST', 'http://localhost:11435')
        self.current_model = "llama3.1:8b"
        self.available_models_info = {
            "llama3.1:8b": "Fast and efficient 8B model - good for general tasks",
            "llama3.1:70b": "Large 70B model - excellent for complex reasoning",
            "qwen2:72b": "Advanced 72B model - superior reasoning capabilities", 
            "codellama:34b": "Specialized 34B model - optimized for code and technical content"
        }
    
    async def generate_response(self, prompt: str, model: str = None) -> str:
        """Generate a response using Ollama"""
        import requests
        
        if not model:
            model = self.current_model
        
        try:
            data = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": 1000,
                    "temperature": 0.7
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '')
            else:
                logger.error(f"Generation failed: {response.status_code} - {response.text}")
                return f"Error: Failed to generate response (status: {response.status_code})"
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Error: {str(e)}"
    
    async def health_check(self):
        """Check Ollama health"""
        import requests
        
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                models = [model['name'] for model in data.get('models', [])]
                return {
                    'status': 'healthy',
                    'ollama_connected': True,
                    'models_available': len(models),
                    'available_models': models,
                    'current_model': self.current_model,
                    'last_check': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'unhealthy',
                    'ollama_connected': False,
                    'error': f"HTTP {response.status_code}",
                    'last_check': datetime.now().isoformat()
                }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'ollama_connected': False,
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }

# Global Ollama service instance
import os
print(f"DEBUG: Creating Ollama service with OLLAMA_HOST={os.getenv('OLLAMA_HOST')}")
ollama_service = SimpleOllamaService()
print(f"DEBUG: Ollama service base_url={ollama_service.base_url}")

# Chat endpoints
@app.post("/chat/message")
async def chat_message_endpoint(request: Request):
    """Chat message endpoint that matches frontend API calls"""
    try:
        data = await request.json()
        message = data.get("message", "")
        context = data.get("context", {})
        dataset = context.get("dataset", "ai_scholar")
        
        logger.info(f"Received chat message: {message[:100]}...")
        
        # Create a context-aware prompt
        if dataset == "ai_scholar":
            system_prompt = "You are an AI research assistant specializing in scientific literature and academic research. Please provide helpful, accurate responses about research topics, methodologies, and academic concepts."
        else:  # quant_finance
            system_prompt = "You are a quantitative finance assistant specializing in financial modeling, trading strategies, and risk analysis. Please provide helpful, accurate responses about finance and trading topics."
        
        full_prompt = f"{system_prompt}\n\nUser question: {message}\n\nResponse:"
        
        try:
            # Generate response using Ollama
            ai_response = await ollama_service.generate_response(full_prompt)
            
            response = {
                "response": ai_response,
                "sources": [],
                "reasoning": f"Generated using Ollama for {dataset} dataset",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "success",
                "dataset": dataset,
                "confidence": 0.8
            }
        except Exception as ollama_error:
            logger.error(f"Ollama error: {ollama_error}")
            response = {
                "response": f"I understand you're asking: '{message}'. I'm having trouble connecting to the AI model right now. Please ensure Ollama is running on localhost:11435 with models like 'llama3.1:8b' or 'llama2' available. You can check with 'ollama list'.",
                "sources": [],
                "reasoning": "Fallback response due to AI model unavailability",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "partial_success",
                "dataset": dataset,
                "error_details": str(ollama_error)
            }
        
        return JSONResponse(content=jsonable_encoder(response))
    except Exception as e:
        logger.error(f"Chat message endpoint error: {e}")
        error_response = {
            "response": "I'm sorry, there was an error processing your message. Please try again.",
            "sources": [],
            "reasoning": "Error occurred during processing",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "error",
            "error": str(e)
        }
        return JSONResponse(content=jsonable_encoder(error_response))

@app.get("/api/chat/health")
async def chat_health():
    """Chat service health check"""
    ollama_health = await ollama_service.health_check()
    
    response = {
        "status": "ok" if ollama_health.get('status') == 'healthy' else "degraded",
        "message": "Chat service is running",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "features": ["basic_chat", "research_assistance", "dataset_switching"],
        "ollama_status": ollama_health,
        "available_datasets": ["ai_scholar", "quant_finance"]
    }
    return JSONResponse(content=jsonable_encoder(response))

@app.get("/api/chat/datasets")
async def get_available_datasets():
    """Get available datasets for chat"""
    datasets = {
        "ai_scholar": {
            "name": "AI Scholar",
            "description": "Scientific research papers and academic literature",
            "features": ["research_analysis", "academic_assistance"]
        },
        "quant_finance": {
            "name": "Quant Scholar", 
            "description": "Quantitative finance and trading research",
            "features": ["financial_modeling", "trading_strategies", "risk_analysis"]
        }
    }
    return JSONResponse(content=jsonable_encoder(datasets))

@app.post("/api/chat/switch-dataset")
async def switch_dataset(request: Request):
    """Switch between AI Scholar and Quant Scholar datasets"""
    try:
        data = await request.json()
        dataset = data.get("dataset", "ai_scholar")
        
        if dataset not in ["ai_scholar", "quant_finance"]:
            raise HTTPException(status_code=400, detail="Invalid dataset. Choose 'ai_scholar' or 'quant_finance'")
        
        response = {
            "message": f"Switched to {dataset.replace('_', ' ').title()} dataset",
            "dataset": dataset,
            "description": "AI Scholar - Scientific research papers" if dataset == "ai_scholar" else "Quant Scholar - Quantitative finance research",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        return JSONResponse(content=jsonable_encoder(response))
    except Exception as e:
        logger.error(f"Dataset switch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "AI Scholar Chat Backend is running", "version": "1.0.0"}

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok"}

@app.get("/api/models")
async def get_available_models():
    """Get available Ollama models"""
    try:
        health_status = await ollama_service.health_check()
        
        return {
            "current_model": ollama_service.current_model,
            "available_models": health_status.get('available_models', []),
            "model_info": ollama_service.available_models_info,
            "status": "success"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to get models",
            "status": "error"
        }

@app.post("/api/models/switch")
async def switch_model(request: Request):
    """Switch the active Ollama model"""
    try:
        data = await request.json()
        model_name = data.get("model")
        
        if not model_name:
            raise HTTPException(status_code=400, detail="Model name is required")
        
        # Check if model is available
        health_status = await ollama_service.health_check()
        available_models = health_status.get('available_models', [])
        
        if model_name not in available_models:
            raise HTTPException(
                status_code=400, 
                detail=f"Model '{model_name}' not available. Available models: {available_models}"
            )
        
        # Switch model
        ollama_service.current_model = model_name
        
        return {
            "message": f"Switched to model: {model_name}",
            "current_model": model_name,
            "model_info": ollama_service.available_models_info.get(model_name, "Model information not available"),
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Model switch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/debug/ollama")
async def debug_ollama():
    """Debug Ollama connectivity"""
    try:
        health_status = await ollama_service.health_check()
        
        # Test a simple generation
        test_response = None
        try:
            test_response = await ollama_service.generate_response(
                "Hello, this is a test. Please respond with 'Ollama is working!'"
            )
        except Exception as gen_error:
            test_response = f"Generation failed: {str(gen_error)}"
        
        return {
            "ollama_health": health_status,
            "test_generation": test_response,
            "base_url": ollama_service.base_url,
            "current_model": ollama_service.current_model,
            "available_models_info": ollama_service.available_models_info
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to connect to Ollama service"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)