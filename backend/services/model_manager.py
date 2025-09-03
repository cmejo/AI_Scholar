"""
AI Model Management System for AI Scholar
Handles model versioning, A/B testing, and performance optimization
"""

import asyncio
import json
import time
import hashlib
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
import random

logger = logging.getLogger(__name__)

class ModelType(Enum):
    """Types of AI models"""
    EMBEDDING = "embedding"
    LLM = "llm"
    SUMMARIZATION = "summarization"
    CLASSIFICATION = "classification"
    TRANSLATION = "translation"

@dataclass
class ModelConfig:
    """Configuration for an AI model"""
    name: str
    model_type: ModelType
    version: str
    endpoint: Optional[str] = None
    api_key: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: float = 0.7
    timeout: int = 30
    cost_per_token: float = 0.0
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ModelPerformance:
    """Performance metrics for a model"""
    model_name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    avg_confidence: float = 0.0
    total_cost: float = 0.0
    last_used: Optional[float] = None
    response_times: List[float] = field(default_factory=list)
    confidence_scores: List[float] = field(default_factory=list)

class ModelManager:
    """Comprehensive AI model management system"""
    
    def __init__(self):
        self.models: Dict[str, ModelConfig] = {}
        self.performance: Dict[str, ModelPerformance] = {}
        self.ab_test_configs: Dict[str, Dict] = {}
        self.user_model_assignments: Dict[str, Dict[str, str]] = {}
        
        # Initialize default models
        self._initialize_default_models()
    
    def _initialize_default_models(self):
        """Initialize default model configurations"""
        default_models = [
            ModelConfig(
                name="embedding_v1",
                model_type=ModelType.EMBEDDING,
                version="1.0",
                endpoint="sentence-transformers/all-MiniLM-L6-v2",
                metadata={"dimensions": 384, "max_sequence_length": 256}
            ),
            ModelConfig(
                name="embedding_v2",
                model_type=ModelType.EMBEDDING,
                version="2.0",
                endpoint="sentence-transformers/all-mpnet-base-v2",
                metadata={"dimensions": 768, "max_sequence_length": 384}
            ),
            ModelConfig(
                name="llm_gpt4",
                model_type=ModelType.LLM,
                version="1.0",
                endpoint="gpt-4-turbo-preview",
                max_tokens=4096,
                cost_per_token=0.00003,
                metadata={"context_window": 128000}
            ),
            ModelConfig(
                name="llm_claude",
                model_type=ModelType.LLM,
                version="1.0",
                endpoint="claude-3-sonnet-20240229",
                max_tokens=4096,
                cost_per_token=0.000015,
                metadata={"context_window": 200000}
            ),
            ModelConfig(
                name="summarization_v1",
                model_type=ModelType.SUMMARIZATION,
                version="1.0",
                endpoint="facebook/bart-large-cnn",
                max_tokens=1024,
                metadata={"max_input_length": 1024}
            )
        ]
        
        for model in default_models:
            self.register_model(model)
    
    def register_model(self, model_config: ModelConfig):
        """Register a new model"""
        self.models[model_config.name] = model_config
        self.performance[model_config.name] = ModelPerformance(model_config.name)
        logger.info(f"Registered model: {model_config.name} ({model_config.model_type.value})")
    
    def get_model(self, model_name: str) -> Optional[ModelConfig]:
        """Get model configuration"""
        return self.models.get(model_name)
    
    def get_models_by_type(self, model_type: ModelType) -> List[ModelConfig]:
        """Get all models of a specific type"""
        return [model for model in self.models.values() if model.model_type == model_type]
    
    def setup_ab_test(self, test_name: str, model_a: str, model_b: str, 
                     traffic_split: float = 0.5, criteria: Dict[str, Any] = None):
        """Set up A/B test between two models"""
        if model_a not in self.models or model_b not in self.models:
            raise ValueError("Both models must be registered")
        
        self.ab_test_configs[test_name] = {
            "model_a": model_a,
            "model_b": model_b,
            "traffic_split": traffic_split,
            "criteria": criteria or {},
            "start_time": time.time(),
            "results": {"a": [], "b": []}
        }
        
        logger.info(f"A/B test '{test_name}' set up: {model_a} vs {model_b}")
    
    async def ab_test_models(self, test_name: str, user_id: str, operation: Callable, *args, **kwargs) -> Any:
        """Execute A/B test for models"""
        if test_name not in self.ab_test_configs:
            raise ValueError(f"A/B test '{test_name}' not found")
        
        test_config = self.ab_test_configs[test_name]
        
        # Determine which model to use
        user_hash = hashlib.md5(f"{user_id}:{test_name}".encode()).hexdigest()
        hash_value = int(user_hash[:8], 16) / 0xffffffff
        
        if hash_value < test_config["traffic_split"]:
            model_name = test_config["model_a"]
            variant = "a"
        else:
            model_name = test_config["model_b"]
            variant = "b"
        
        # Execute operation with selected model
        start_time = time.time()
        try:
            result = await operation(model_name, *args, **kwargs)
            execution_time = time.time() - start_time
            
            # Record A/B test result
            test_result = {
                "user_id": user_id,
                "model": model_name,
                "variant": variant,
                "execution_time": execution_time,
                "success": True,
                "timestamp": time.time()
            }
            
            # Add result-specific metrics if available
            if isinstance(result, dict):
                if "confidence" in result:
                    test_result["confidence"] = result["confidence"]
                if "quality_score" in result:
                    test_result["quality_score"] = result["quality_score"]
            
            test_config["results"][variant].append(test_result)
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Record failure
            test_result = {
                "user_id": user_id,
                "model": model_name,
                "variant": variant,
                "execution_time": execution_time,
                "success": False,
                "error": str(e),
                "timestamp": time.time()
            }
            
            test_config["results"][variant].append(test_result)
            raise
    
    def get_ab_test_results(self, test_name: str) -> Dict[str, Any]:
        """Get A/B test results and analysis"""
        if test_name not in self.ab_test_configs:
            raise ValueError(f"A/B test '{test_name}' not found")
        
        test_config = self.ab_test_configs[test_name]
        results_a = test_config["results"]["a"]
        results_b = test_config["results"]["b"]
        
        def analyze_variant(results: List[Dict]) -> Dict[str, Any]:
            if not results:
                return {"count": 0}
            
            successful = [r for r in results if r["success"]]
            failed = [r for r in results if not r["success"]]
            
            analysis = {
                "count": len(results),
                "success_count": len(successful),
                "failure_count": len(failed),
                "success_rate": len(successful) / len(results),
                "avg_response_time": sum(r["execution_time"] for r in results) / len(results)
            }
            
            # Calculate confidence metrics if available
            confidence_scores = [r["confidence"] for r in successful if "confidence" in r]
            if confidence_scores:
                analysis["avg_confidence"] = sum(confidence_scores) / len(confidence_scores)
            
            return analysis
        
        analysis_a = analyze_variant(results_a)
        analysis_b = analyze_variant(results_b)
        
        # Determine winner
        winner = None
        if analysis_a["count"] > 0 and analysis_b["count"] > 0:
            # Simple winner determination based on success rate and response time
            score_a = analysis_a["success_rate"] - (analysis_a["avg_response_time"] / 10)
            score_b = analysis_b["success_rate"] - (analysis_b["avg_response_time"] / 10)
            
            if abs(score_a - score_b) > 0.05:  # 5% threshold
                winner = "a" if score_a > score_b else "b"
        
        return {
            "test_name": test_name,
            "model_a": test_config["model_a"],
            "model_b": test_config["model_b"],
            "traffic_split": test_config["traffic_split"],
            "start_time": test_config["start_time"],
            "duration_hours": (time.time() - test_config["start_time"]) / 3600,
            "variant_a": analysis_a,
            "variant_b": analysis_b,
            "winner": winner,
            "recommendation": self._get_ab_test_recommendation(analysis_a, analysis_b, winner)
        }
    
    def _get_ab_test_recommendation(self, analysis_a: Dict, analysis_b: Dict, winner: Optional[str]) -> str:
        """Get recommendation based on A/B test results"""
        if not winner:
            return "Continue testing - no clear winner yet"
        
        winning_analysis = analysis_a if winner == "a" else analysis_b
        losing_analysis = analysis_b if winner == "a" else analysis_a
        
        if winning_analysis["success_rate"] > losing_analysis["success_rate"] + 0.1:
            return f"Model {winner.upper()} shows significantly better success rate"
        elif winning_analysis["avg_response_time"] < losing_analysis["avg_response_time"] * 0.8:
            return f"Model {winner.upper()} is significantly faster"
        else:
            return f"Model {winner.upper()} shows marginal improvement"
    
    async def evaluate_model_performance(self, model_name: str, time_range_hours: int = 24) -> Dict[str, Any]:
        """Evaluate comprehensive model performance"""
        if model_name not in self.performance:
            raise ValueError(f"Model '{model_name}' not found")
        
        perf = self.performance[model_name]
        
        # Calculate recent performance (last N hours)
        cutoff_time = time.time() - (time_range_hours * 3600)
        recent_times = [t for t in perf.response_times if t > cutoff_time]
        recent_confidence = [c for c in perf.confidence_scores if c > cutoff_time]
        
        evaluation = {
            "model_name": model_name,
            "time_range_hours": time_range_hours,
            "total_requests": perf.total_requests,
            "success_rate": perf.successful_requests / max(perf.total_requests, 1),
            "avg_response_time": perf.avg_response_time,
            "avg_confidence": perf.avg_confidence,
            "total_cost": perf.total_cost,
            "last_used": perf.last_used,
            "recent_performance": {
                "request_count": len(recent_times),
                "avg_response_time": sum(recent_times) / len(recent_times) if recent_times else 0,
                "avg_confidence": sum(recent_confidence) / len(recent_confidence) if recent_confidence else 0
            }
        }
        
        # Performance grade
        grade = self._calculate_performance_grade(evaluation)
        evaluation["performance_grade"] = grade
        
        return evaluation
    
    def _calculate_performance_grade(self, evaluation: Dict[str, Any]) -> str:
        """Calculate performance grade for model"""
        score = 0
        
        # Success rate (40% of score)
        success_rate = evaluation["success_rate"]
        if success_rate >= 0.99:
            score += 40
        elif success_rate >= 0.95:
            score += 35
        elif success_rate >= 0.90:
            score += 30
        else:
            score += max(0, success_rate * 30)
        
        # Response time (30% of score)
        response_time = evaluation["avg_response_time"]
        if response_time <= 1.0:
            score += 30
        elif response_time <= 2.0:
            score += 25
        elif response_time <= 5.0:
            score += 20
        else:
            score += max(0, 30 - (response_time - 5) * 2)
        
        # Confidence (30% of score)
        confidence = evaluation["avg_confidence"]
        if confidence >= 0.9:
            score += 30
        elif confidence >= 0.8:
            score += 25
        elif confidence >= 0.7:
            score += 20
        else:
            score += max(0, confidence * 30)
        
        # Convert to letter grade
        if score >= 90:
            return "A+"
        elif score >= 85:
            return "A"
        elif score >= 80:
            return "B+"
        elif score >= 75:
            return "B"
        elif score >= 70:
            return "C+"
        elif score >= 65:
            return "C"
        else:
            return "D"
    
    async def record_model_usage(self, model_name: str, response_time: float, 
                                success: bool, confidence: Optional[float] = None,
                                tokens_used: int = 0):
        """Record model usage statistics"""
        if model_name not in self.performance:
            self.performance[model_name] = ModelPerformance(model_name)
        
        perf = self.performance[model_name]
        
        # Update counters
        perf.total_requests += 1
        if success:
            perf.successful_requests += 1
        else:
            perf.failed_requests += 1
        
        # Update response time
        perf.response_times.append(response_time)
        if len(perf.response_times) > 1000:  # Keep only recent times
            perf.response_times = perf.response_times[-1000:]
        
        perf.avg_response_time = sum(perf.response_times) / len(perf.response_times)
        
        # Update confidence
        if confidence is not None:
            perf.confidence_scores.append(confidence)
            if len(perf.confidence_scores) > 1000:
                perf.confidence_scores = perf.confidence_scores[-1000:]
            perf.avg_confidence = sum(perf.confidence_scores) / len(perf.confidence_scores)
        
        # Update cost
        if model_name in self.models:
            model_config = self.models[model_name]
            perf.total_cost += tokens_used * model_config.cost_per_token
        
        perf.last_used = time.time()
    
    def get_user_model_version(self, user_id: str, model_type: ModelType) -> str:
        """Get assigned model version for user"""
        if user_id not in self.user_model_assignments:
            self.user_model_assignments[user_id] = {}
        
        type_key = model_type.value
        if type_key not in self.user_model_assignments[user_id]:
            # Assign model based on A/B test or default
            available_models = self.get_models_by_type(model_type)
            if available_models:
                # Simple assignment - could be more sophisticated
                model_name = available_models[0].name
                self.user_model_assignments[user_id][type_key] = model_name
            else:
                raise ValueError(f"No models available for type {model_type.value}")
        
        return self.user_model_assignments[user_id][type_key]
    
    async def query_model(self, model_name: str, input_data: Any, **kwargs) -> Dict[str, Any]:
        """Query a specific model"""
        if model_name not in self.models:
            raise ValueError(f"Model '{model_name}' not found")
        
        model_config = self.models[model_name]
        if not model_config.enabled:
            raise ValueError(f"Model '{model_name}' is disabled")
        
        start_time = time.time()
        
        try:
            # This would integrate with your actual AI services
            # For now, we'll simulate the response
            await asyncio.sleep(0.1 + random.random() * 0.2)  # Simulate processing time
            
            # Mock response based on model type
            if model_config.model_type == ModelType.EMBEDDING:
                result = {
                    "embeddings": [random.random() for _ in range(model_config.metadata.get("dimensions", 384))],
                    "model": model_name,
                    "confidence": 0.9 + random.random() * 0.1
                }
            elif model_config.model_type == ModelType.LLM:
                result = {
                    "response": f"Response from {model_name}: {input_data}",
                    "model": model_name,
                    "confidence": 0.8 + random.random() * 0.2,
                    "tokens_used": len(str(input_data)) // 4  # Rough token estimate
                }
            else:
                result = {
                    "output": f"Processed by {model_name}",
                    "model": model_name,
                    "confidence": 0.85 + random.random() * 0.15
                }
            
            # Record successful usage
            response_time = time.time() - start_time
            await self.record_model_usage(
                model_name, 
                response_time, 
                True, 
                result.get("confidence"),
                result.get("tokens_used", 0)
            )
            
            return result
            
        except Exception as e:
            # Record failed usage
            response_time = time.time() - start_time
            await self.record_model_usage(model_name, response_time, False)
            raise
    
    def get_model_recommendations(self) -> List[Dict[str, Any]]:
        """Get model optimization recommendations"""
        recommendations = []
        
        for model_name, perf in self.performance.items():
            if perf.total_requests < 10:
                continue  # Skip models with insufficient data
            
            model_config = self.models[model_name]
            
            # Performance-based recommendations
            if perf.avg_response_time > 5.0:
                recommendations.append({
                    "type": "performance",
                    "model": model_name,
                    "issue": "Slow response time",
                    "current_value": f"{perf.avg_response_time:.2f}s",
                    "recommendation": "Consider switching to a faster model or optimizing parameters"
                })
            
            if perf.successful_requests / perf.total_requests < 0.95:
                recommendations.append({
                    "type": "reliability",
                    "model": model_name,
                    "issue": "Low success rate",
                    "current_value": f"{(perf.successful_requests / perf.total_requests) * 100:.1f}%",
                    "recommendation": "Investigate error patterns and consider model replacement"
                })
            
            # Cost-based recommendations
            if model_config.cost_per_token > 0 and perf.total_cost > 100:
                recommendations.append({
                    "type": "cost",
                    "model": model_name,
                    "issue": "High usage cost",
                    "current_value": f"${perf.total_cost:.2f}",
                    "recommendation": "Consider switching to a more cost-effective model"
                })
        
        return recommendations
    
    def export_model_performance(self, output_file: str) -> bool:
        """Export model performance data"""
        try:
            export_data = {
                "timestamp": time.time(),
                "models": {name: config.__dict__ for name, config in self.models.items()},
                "performance": {name: perf.__dict__ for name, perf in self.performance.items()},
                "ab_tests": self.ab_test_configs,
                "recommendations": self.get_model_recommendations()
            }
            
            with open(output_file, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            logger.info(f"Model performance data exported to {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting model performance: {e}")
            return False

# Global model manager instance
model_manager = ModelManager()

# Convenience functions
async def get_best_model_for_task(model_type: ModelType, user_id: str = None) -> str:
    """Get the best performing model for a task"""
    models = model_manager.get_models_by_type(model_type)
    
    if not models:
        raise ValueError(f"No models available for type {model_type.value}")
    
    if len(models) == 1:
        return models[0].name
    
    # Return model with best performance
    best_model = None
    best_score = -1
    
    for model in models:
        if model.name in model_manager.performance:
            perf = model_manager.performance[model.name]
            if perf.total_requests > 0:
                # Simple scoring: success_rate - (response_time / 10)
                score = (perf.successful_requests / perf.total_requests) - (perf.avg_response_time / 10)
                if score > best_score:
                    best_score = score
                    best_model = model.name
    
    return best_model or models[0].name

async def smart_model_query(model_type: ModelType, input_data: Any, user_id: str = None, **kwargs) -> Dict[str, Any]:
    """Smart model querying with automatic model selection"""
    model_name = await get_best_model_for_task(model_type, user_id)
    return await model_manager.query_model(model_name, input_data, **kwargs)

# Usage example
if __name__ == "__main__":
    async def test_model_manager():
        # Test model querying
        result = await model_manager.query_model("llm_gpt4", "What is machine learning?")
        print(f"LLM Result: {result}")
        
        # Test A/B testing
        model_manager.setup_ab_test("embedding_test", "embedding_v1", "embedding_v2")
        
        # Simulate A/B test usage
        for i in range(20):
            user_id = f"user_{i % 5}"  # 5 different users
            result = await model_manager.ab_test_models(
                "embedding_test",
                user_id,
                model_manager.query_model,
                f"Test input {i}"
            )
        
        # Get A/B test results
        ab_results = model_manager.get_ab_test_results("embedding_test")
        print(f"A/B Test Results: {json.dumps(ab_results, indent=2, default=str)}")
        
        # Get model recommendations
        recommendations = model_manager.get_model_recommendations()
        print(f"Model Recommendations: {recommendations}")
        
        # Export performance data
        success = model_manager.export_model_performance("model_performance.json")
        print(f"Export successful: {success}")
    
    # Run test
    asyncio.run(test_model_manager())