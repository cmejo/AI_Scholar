"""
Ollama Service for AI Scholar RAG System
Handles local LLM interactions for scientific literature queries
"""

import requests
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class OllamaService:
    """Service for interacting with Ollama local LLM server"""
    
    def __init__(self, base_url: str = "http://ollama:11434"):
        self.base_url = base_url
        self.available_models = []
        self.current_model = "llama3.1:8b"  # Default to latest model
        self.scientific_models = {
            # Latest State-of-the-Art Models (2024)
            "llama3.1:8b": "Latest Llama 3.1 8B - Excellent for scientific reasoning and analysis",
            "llama3.1:70b": "Llama 3.1 70B - Most capable model for complex scientific queries",
            "mistral:7b-v0.3": "Mistral 7B v0.3 - Fast and efficient for scientific analysis",
            "codellama:34b": "CodeLlama 34B - Specialized for technical and code analysis",
            "phi3:medium": "Phi-3 Medium - Microsoft's efficient model for scientific tasks",
            "qwen2:7b": "Qwen2 7B - Alibaba's model with strong reasoning capabilities",
            "qwen2:72b": "Qwen2 72B - Large model for complex scientific analysis",
            "gemma2:9b": "Gemma 2 9B - Google's efficient model for research tasks",
            "gemma2:27b": "Gemma 2 27B - Large Google model for comprehensive analysis",
            
            # Legacy Models (still supported)
            "llama2": "General purpose model, good for scientific reasoning",
            "mistral": "Fast and efficient, good for scientific analysis", 
            "codellama": "Specialized for code and technical content",
            "llama2:13b": "Larger model for complex scientific queries",
            "mistral:7b": "Balanced performance for scientific tasks"
        }
    
    async def initialize(self):
        """Initialize Ollama service and check available models"""
        try:
            await self.check_health()
            await self.list_models()
            await self.ensure_scientific_models()
            logger.info(f"Ollama service initialized with {len(self.available_models)} models")
        except Exception as e:
            logger.error(f"Failed to initialize Ollama service: {e}")
            raise
    
    async def check_health(self) -> bool:
        """Check if Ollama service is healthy"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False
    
    async def list_models(self) -> List[str]:
        """List available models in Ollama"""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                self.available_models = [model['name'] for model in data.get('models', [])]
                return self.available_models
            else:
                logger.error(f"Failed to list models: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []
    
    async def ensure_scientific_models(self):
        """Ensure required scientific models are available"""
        # Priority models to ensure are available
        priority_models = [
            "llama3.1:8b",      # Default model
            "mistral:7b-v0.3",  # Fast alternative
            "codellama:34b",    # For technical content
            "phi3:medium",      # Efficient option
            "qwen2:7b"          # Strong reasoning
        ]
        
        # Try to ensure at least the default model is available
        for model in priority_models:
            if not any(model in available for available in self.available_models):
                logger.info(f"Pulling priority model: {model}")
                success = await self.pull_model(model)
                if success:
                    break  # At least one model is available
                    
        # Optionally pull larger models if resources allow
        optional_models = ["llama3.1:70b", "qwen2:72b", "gemma2:27b"]
        for model in optional_models:
            if not any(model in available for available in self.available_models):
                logger.info(f"Optional model {model} not available - can be pulled on demand")
    
    async def pull_model(self, model_name: str) -> bool:
        """Pull a model from Ollama registry"""
        try:
            logger.info(f"Pulling model {model_name}...")
            response = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": model_name},
                stream=True,
                timeout=300  # 5 minutes timeout for model download
            )
            
            if response.status_code == 200:
                # Stream the download progress
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line)
                        if data.get('status') == 'success':
                            logger.info(f"Successfully pulled model {model_name}")
                            await self.list_models()  # Refresh model list
                            return True
                        elif 'error' in data:
                            logger.error(f"Error pulling model {model_name}: {data['error']}")
                            return False
            return False
        except Exception as e:
            logger.error(f"Failed to pull model {model_name}: {e}")
            return False
    
    def get_recommended_model(self, query_type: str = "general") -> str:
        """Get recommended model based on query type"""
        recommendations = {
            "general": ["llama3.1:8b", "mistral:7b-v0.3", "phi3:medium"],
            "complex": ["llama3.1:70b", "qwen2:72b", "gemma2:27b"],
            "technical": ["codellama:34b", "llama3.1:8b", "qwen2:7b"],
            "fast": ["phi3:medium", "mistral:7b-v0.3", "qwen2:7b"],
            "reasoning": ["qwen2:7b", "llama3.1:8b", "gemma2:9b"]
        }
        
        preferred_models = recommendations.get(query_type, recommendations["general"])
        
        # Return first available model from preferences
        for model in preferred_models:
            if any(model in available for available in self.available_models):
                return model
                
        # Fallback to current model
        return self.current_model
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get detailed information about a model"""
        if model_name in self.scientific_models:
            return {
                "name": model_name,
                "description": self.scientific_models[model_name],
                "available": any(model_name in available for available in self.available_models),
                "type": self._get_model_type(model_name),
                "size": self._get_model_size(model_name),
                "performance": self._get_model_performance(model_name)
            }
        return {"name": model_name, "description": "Unknown model", "available": False}
    
    def _get_model_type(self, model_name: str) -> str:
        """Determine model type based on name"""
        if "codellama" in model_name.lower():
            return "code"
        elif "phi3" in model_name.lower():
            return "efficient"
        elif "qwen" in model_name.lower():
            return "reasoning"
        elif "gemma" in model_name.lower():
            return "research"
        elif "mistral" in model_name.lower():
            return "fast"
        elif "llama" in model_name.lower():
            return "general"
        return "unknown"
    
    def _get_model_size(self, model_name: str) -> str:
        """Extract model size from name"""
        if "70b" in model_name.lower() or "72b" in model_name.lower():
            return "large"
        elif "34b" in model_name.lower() or "27b" in model_name.lower():
            return "medium-large"
        elif "13b" in model_name.lower() or "9b" in model_name.lower():
            return "medium"
        elif "7b" in model_name.lower() or "8b" in model_name.lower():
            return "small-medium"
        return "unknown"
    
    def _get_model_performance(self, model_name: str) -> Dict[str, str]:
        """Get performance characteristics of model"""
        performance_map = {
            "llama3.1:8b": {"speed": "fast", "quality": "high", "memory": "medium"},
            "llama3.1:70b": {"speed": "slow", "quality": "excellent", "memory": "high"},
            "mistral:7b-v0.3": {"speed": "very-fast", "quality": "good", "memory": "low"},
            "codellama:34b": {"speed": "medium", "quality": "high", "memory": "high"},
            "phi3:medium": {"speed": "fast", "quality": "good", "memory": "low"},
            "qwen2:7b": {"speed": "fast", "quality": "high", "memory": "medium"},
            "qwen2:72b": {"speed": "slow", "quality": "excellent", "memory": "high"},
            "gemma2:9b": {"speed": "fast", "quality": "good", "memory": "medium"},
            "gemma2:27b": {"speed": "medium", "quality": "high", "memory": "high"}
        }
        return performance_map.get(model_name, {"speed": "unknown", "quality": "unknown", "memory": "unknown"})
    
    async def generate_scientific_response(
        self, 
        query: str, 
        context_chunks: List[str], 
        model: str = None,
        temperature: float = 0.3,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """Generate response using Ollama LLM with scientific context"""
        
        model = model or self.current_model
        
        # Ensure model is available
        if model not in self.available_models:
            logger.warning(f"Model {model} not available, using {self.current_model}")
            model = self.current_model
        
        # Build scientific prompt with context
        scientific_prompt = self._build_scientific_prompt(query, context_chunks)
        
        try:
            start_time = datetime.now()
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": scientific_prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "top_p": 0.9,
                        "max_tokens": max_tokens,
                        "stop": ["Human:", "Assistant:", "Query:"]
                    }
                },
                timeout=120  # 2 minutes timeout
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            if response.status_code == 200:
                result = response.json()
                
                return {
                    'response': result['response'].strip(),
                    'model': model,
                    'context_chunks_used': len(context_chunks),
                    'prompt_tokens': len(scientific_prompt.split()),
                    'processing_time': processing_time,
                    'citations': self._extract_citations_from_context(context_chunks),
                    'confidence_score': self._calculate_confidence_score(result.get('response', '')),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise
    
    def _build_scientific_prompt(self, query: str, context_chunks: List[str]) -> str:
        """Build scientific research prompt with context"""
        
        # Limit context to prevent token overflow
        max_context_length = 8000  # Adjust based on model capacity
        context_text = ""
        
        for i, chunk in enumerate(context_chunks[:10]):  # Limit to 10 chunks
            chunk_text = f"\n\n[Source {i+1}]\n{chunk}"
            if len(context_text + chunk_text) > max_context_length:
                break
            context_text += chunk_text
        
        prompt = f"""You are a scientific research assistant with expertise in analyzing peer-reviewed literature. Your task is to provide accurate, evidence-based responses to research questions using the provided scientific sources.

SCIENTIFIC SOURCES:
{context_text}

RESEARCH QUESTION: {query}

INSTRUCTIONS:
1. Provide a comprehensive, accurate answer based ONLY on the provided sources
2. Use [Source X] citations to reference specific sources
3. Highlight key findings, methodologies, and conclusions
4. Note any limitations, uncertainties, or conflicting evidence
5. If the sources don't contain enough information, clearly state this
6. Maintain scientific rigor and objectivity
7. Use appropriate scientific terminology

RESPONSE:"""
        
        return prompt
    
    def _extract_citations_from_context(self, context_chunks: List[str]) -> List[Dict[str, str]]:
        """Extract citation information from context chunks"""
        citations = []
        
        for i, chunk in enumerate(context_chunks):
            # Simple citation extraction - can be enhanced with more sophisticated parsing
            citation = {
                'source_id': f"Source {i+1}",
                'text_preview': chunk[:200] + "..." if len(chunk) > 200 else chunk,
                'relevance': 'high'  # This could be calculated based on similarity scores
            }
            citations.append(citation)
        
        return citations
    
    def _calculate_confidence_score(self, response: str) -> float:
        """Calculate confidence score based on response characteristics"""
        # Simple heuristic - can be enhanced with more sophisticated analysis
        confidence = 0.5  # Base confidence
        
        # Increase confidence for citations
        citation_count = response.count('[Source')
        confidence += min(citation_count * 0.1, 0.3)
        
        # Increase confidence for scientific terms
        scientific_terms = ['study', 'research', 'analysis', 'findings', 'methodology', 'results']
        term_count = sum(1 for term in scientific_terms if term.lower() in response.lower())
        confidence += min(term_count * 0.05, 0.2)
        
        # Decrease confidence for uncertainty phrases
        uncertainty_phrases = ['unclear', 'uncertain', 'may be', 'possibly', 'not enough information']
        uncertainty_count = sum(1 for phrase in uncertainty_phrases if phrase.lower() in response.lower())
        confidence -= min(uncertainty_count * 0.1, 0.3)
        
        return max(0.1, min(1.0, confidence))
    
    async def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific model"""
        try:
            response = requests.post(
                f"{self.base_url}/api/show",
                json={"name": model_name}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {}
        except Exception as e:
            logger.error(f"Error getting model info for {model_name}: {e}")
            return {}
    
    def set_model(self, model_name: str) -> bool:
        """Set the current model for generation"""
        if model_name in self.available_models:
            self.current_model = model_name
            logger.info(f"Switched to model: {model_name}")
            return True
        else:
            logger.error(f"Model {model_name} not available")
            return False
    
    def get_available_models(self) -> Dict[str, str]:
        """Get available models with descriptions"""
        available = {}
        for model in self.available_models:
            description = self.scientific_models.get(
                model, 
                "Available model for scientific queries"
            )
            available[model] = description
        return available
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the Ollama service"""
        health_status = {
            'status': 'unknown',
            'ollama_connected': False,
            'models_available': 0,
            'current_model': self.current_model,
            'last_check': datetime.now().isoformat()
        }
        
        try:
            # Test connection by listing models
            models = await self.list_models()
            health_status['ollama_connected'] = True
            health_status['models_available'] = len(models)
            health_status['status'] = 'healthy'
            
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            health_status['status'] = 'unhealthy'
            health_status['error'] = str(e)
        
        return health_status
    
    async def generate_response(
        self, 
        prompt: str, 
        model: str = None,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """Generate a response using the specified model"""
        
        if not model:
            model = self.current_model
        
        try:
            # Prepare the request
            data = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature
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

# Global instance
ollama_service = OllamaService()