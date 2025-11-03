"""
Embedding Service for Multi-Instance Vector Store.

This module handles embedding generation, validation, and optimization
for different scholar instances with configurable models and settings.
"""

import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import numpy as np
from sentence_transformers import SentenceTransformer
import torch
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service for generating and managing embeddings for different scholar instances
    with support for multiple embedding models and quality validation.
    """
    
    def __init__(self):
        self.models: Dict[str, SentenceTransformer] = {}
        self.model_configs: Dict[str, Dict[str, Any]] = {}
        self.embedding_cache: Dict[str, np.ndarray] = {}
        self.cache_enabled = True
        self.max_cache_size = 10000
        
        # Supported embedding models with their characteristics
        self.supported_models = {
            "all-MiniLM-L6-v2": {
                "dimensions": 384,
                "max_seq_length": 256,
                "speed": "fast",
                "quality": "good",
                "description": "Balanced model for general use"
            },
            "all-mpnet-base-v2": {
                "dimensions": 768,
                "max_seq_length": 384,
                "speed": "medium",
                "quality": "high",
                "description": "High quality model for better accuracy"
            },
            "multi-qa-MiniLM-L6-cos-v1": {
                "dimensions": 384,
                "max_seq_length": 512,
                "speed": "fast",
                "quality": "good",
                "description": "Optimized for question-answering tasks"
            },
            "all-distilroberta-v1": {
                "dimensions": 768,
                "max_seq_length": 512,
                "speed": "medium",
                "quality": "high",
                "description": "RoBERTa-based model for scientific text"
            }
        }
    
    async def initialize_model(
        self, 
        model_name: str, 
        instance_name: str,
        device: Optional[str] = None
    ) -> bool:
        """Initialize an embedding model for a specific instance."""
        
        try:
            if model_name not in self.supported_models:
                logger.warning(f"Model {model_name} not in supported models list")
            
            logger.info(f"Loading embedding model {model_name} for instance {instance_name}")
            
            # Determine device
            if device is None:
                device = "cuda" if torch.cuda.is_available() else "cpu"
            
            # Load model
            model = SentenceTransformer(model_name, device=device)
            
            # Store model and configuration
            model_key = f"{instance_name}_{model_name}"
            self.models[model_key] = model
            self.model_configs[model_key] = {
                "model_name": model_name,
                "instance_name": instance_name,
                "device": device,
                "loaded_at": datetime.now().isoformat(),
                "model_info": self.supported_models.get(model_name, {}),
                "max_seq_length": model.max_seq_length
            }
            
            logger.info(f"Successfully loaded {model_name} for {instance_name} on {device}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize model {model_name} for {instance_name}: {e}")
            return False
    
    def _get_model_key(self, instance_name: str, model_name: str) -> str:
        """Generate model key for instance-model combination."""
        return f"{instance_name}_{model_name}"
    
    def _get_cache_key(self, text: str, model_name: str) -> str:
        """Generate cache key for text-model combination."""
        import hashlib
        text_hash = hashlib.md5(text.encode()).hexdigest()
        return f"{model_name}_{text_hash}"
    
    async def generate_embeddings(
        self, 
        texts: List[str], 
        instance_name: str,
        model_name: str,
        batch_size: int = 32,
        show_progress: bool = False
    ) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        
        model_key = self._get_model_key(instance_name, model_name)
        
        if model_key not in self.models:
            # Try to initialize the model
            if not await self.initialize_model(model_name, instance_name):
                raise RuntimeError(f"Model {model_name} not available for {instance_name}")
        
        model = self.models[model_key]
        
        try:
            # Check cache for existing embeddings
            cached_embeddings = {}
            uncached_texts = []
            uncached_indices = []
            
            if self.cache_enabled:
                for i, text in enumerate(texts):
                    cache_key = self._get_cache_key(text, model_name)
                    if cache_key in self.embedding_cache:
                        cached_embeddings[i] = self.embedding_cache[cache_key]
                    else:
                        uncached_texts.append(text)
                        uncached_indices.append(i)
            else:
                uncached_texts = texts
                uncached_indices = list(range(len(texts)))
            
            # Generate embeddings for uncached texts
            new_embeddings = []
            if uncached_texts:
                logger.info(f"Generating embeddings for {len(uncached_texts)} texts using {model_name}")
                
                # Generate embeddings in batches
                embeddings = model.encode(
                    uncached_texts,
                    batch_size=batch_size,
                    show_progress_bar=show_progress,
                    convert_to_tensor=False
                )
                
                new_embeddings = embeddings.tolist()
                
                # Cache new embeddings
                if self.cache_enabled:
                    for text, embedding in zip(uncached_texts, new_embeddings):
                        cache_key = self._get_cache_key(text, model_name)
                        self.embedding_cache[cache_key] = np.array(embedding)
                        
                        # Manage cache size
                        if len(self.embedding_cache) > self.max_cache_size:
                            # Remove oldest entries (simple FIFO)
                            oldest_key = next(iter(self.embedding_cache))
                            del self.embedding_cache[oldest_key]
            
            # Combine cached and new embeddings
            final_embeddings = [None] * len(texts)
            
            # Add cached embeddings
            for i, embedding in cached_embeddings.items():
                final_embeddings[i] = embedding.tolist()
            
            # Add new embeddings
            for i, embedding in zip(uncached_indices, new_embeddings):
                final_embeddings[i] = embedding
            
            logger.info(f"Generated embeddings for {len(texts)} texts ({len(cached_embeddings)} from cache)")
            return final_embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    async def generate_single_embedding(
        self, 
        text: str, 
        instance_name: str,
        model_name: str
    ) -> List[float]:
        """Generate embedding for a single text."""
        
        embeddings = await self.generate_embeddings(
            texts=[text],
            instance_name=instance_name,
            model_name=model_name
        )
        
        return embeddings[0] if embeddings else []
    
    async def validate_embedding_quality(
        self, 
        embeddings: List[List[float]], 
        texts: List[str],
        model_name: str
    ) -> Dict[str, Any]:
        """Validate the quality of generated embeddings."""
        
        validation_result = {
            'valid': True,
            'issues': [],
            'warnings': [],
            'stats': {},
            'quality_score': 0.0
        }
        
        try:
            if not embeddings or not texts:
                validation_result['valid'] = False
                validation_result['issues'].append("Empty embeddings or texts")
                return validation_result
            
            if len(embeddings) != len(texts):
                validation_result['valid'] = False
                validation_result['issues'].append("Mismatch between embeddings and texts count")
                return validation_result
            
            # Convert to numpy arrays for analysis
            embedding_array = np.array(embeddings)
            
            # Basic statistics
            validation_result['stats'] = {
                'embedding_count': len(embeddings),
                'embedding_dimension': len(embeddings[0]) if embeddings else 0,
                'mean_magnitude': float(np.mean(np.linalg.norm(embedding_array, axis=1))),
                'std_magnitude': float(np.std(np.linalg.norm(embedding_array, axis=1))),
                'min_magnitude': float(np.min(np.linalg.norm(embedding_array, axis=1))),
                'max_magnitude': float(np.max(np.linalg.norm(embedding_array, axis=1)))
            }
            
            # Check for zero embeddings
            zero_embeddings = np.sum(np.all(embedding_array == 0, axis=1))
            if zero_embeddings > 0:
                validation_result['issues'].append(f"{zero_embeddings} embeddings are all zeros")
                validation_result['valid'] = False
            
            # Check for NaN or infinite values
            nan_embeddings = np.sum(np.any(np.isnan(embedding_array), axis=1))
            inf_embeddings = np.sum(np.any(np.isinf(embedding_array), axis=1))
            
            if nan_embeddings > 0:
                validation_result['issues'].append(f"{nan_embeddings} embeddings contain NaN values")
                validation_result['valid'] = False
            
            if inf_embeddings > 0:
                validation_result['issues'].append(f"{inf_embeddings} embeddings contain infinite values")
                validation_result['valid'] = False
            
            # Check embedding dimension consistency
            expected_dim = self.supported_models.get(model_name, {}).get('dimensions')
            actual_dim = validation_result['stats']['embedding_dimension']
            
            if expected_dim and actual_dim != expected_dim:
                validation_result['warnings'].append(
                    f"Embedding dimension {actual_dim} doesn't match expected {expected_dim} for {model_name}"
                )
            
            # Check for very low magnitude embeddings (might indicate poor quality)
            low_magnitude_threshold = 0.1
            low_magnitude_count = np.sum(np.linalg.norm(embedding_array, axis=1) < low_magnitude_threshold)
            
            if low_magnitude_count > len(embeddings) * 0.1:  # More than 10%
                validation_result['warnings'].append(
                    f"{low_magnitude_count} embeddings have very low magnitude (< {low_magnitude_threshold})"
                )
            
            # Calculate quality score (0-1)
            quality_factors = []
            
            # Factor 1: No invalid values
            if zero_embeddings == 0 and nan_embeddings == 0 and inf_embeddings == 0:
                quality_factors.append(1.0)
            else:
                invalid_ratio = (zero_embeddings + nan_embeddings + inf_embeddings) / len(embeddings)
                quality_factors.append(max(0.0, 1.0 - invalid_ratio))
            
            # Factor 2: Magnitude distribution
            mean_mag = validation_result['stats']['mean_magnitude']
            if 0.5 <= mean_mag <= 2.0:  # Reasonable range
                quality_factors.append(1.0)
            else:
                quality_factors.append(0.7)
            
            # Factor 3: Dimension correctness
            if expected_dim and actual_dim == expected_dim:
                quality_factors.append(1.0)
            else:
                quality_factors.append(0.8)
            
            validation_result['quality_score'] = np.mean(quality_factors)
            
        except Exception as e:
            validation_result['valid'] = False
            validation_result['issues'].append(f"Validation error: {str(e)}")
            logger.error(f"Error validating embeddings: {e}")
        
        return validation_result
    
    async def compare_embeddings(
        self, 
        embeddings1: List[List[float]], 
        embeddings2: List[List[float]],
        similarity_threshold: float = 0.8
    ) -> Dict[str, Any]:
        """Compare two sets of embeddings for similarity."""
        
        try:
            if len(embeddings1) != len(embeddings2):
                return {
                    'error': 'Embedding sets have different lengths',
                    'comparable': False
                }
            
            # Convert to numpy arrays
            emb1 = np.array(embeddings1)
            emb2 = np.array(embeddings2)
            
            # Calculate cosine similarities
            similarities = []
            for e1, e2 in zip(emb1, emb2):
                # Normalize vectors
                e1_norm = e1 / np.linalg.norm(e1)
                e2_norm = e2 / np.linalg.norm(e2)
                
                # Calculate cosine similarity
                similarity = np.dot(e1_norm, e2_norm)
                similarities.append(float(similarity))
            
            similarities = np.array(similarities)
            
            # Statistics
            comparison_result = {
                'comparable': True,
                'embedding_count': len(similarities),
                'mean_similarity': float(np.mean(similarities)),
                'std_similarity': float(np.std(similarities)),
                'min_similarity': float(np.min(similarities)),
                'max_similarity': float(np.max(similarities)),
                'high_similarity_count': int(np.sum(similarities >= similarity_threshold)),
                'high_similarity_ratio': float(np.sum(similarities >= similarity_threshold) / len(similarities)),
                'similarities': similarities.tolist()
            }
            
            return comparison_result
            
        except Exception as e:
            logger.error(f"Error comparing embeddings: {e}")
            return {
                'error': str(e),
                'comparable': False
            }
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get information about a supported model."""
        return self.supported_models.get(model_name, {})
    
    def list_supported_models(self) -> Dict[str, Dict[str, Any]]:
        """List all supported embedding models."""
        return self.supported_models.copy()
    
    def get_loaded_models(self) -> Dict[str, Dict[str, Any]]:
        """Get information about currently loaded models."""
        return self.model_configs.copy()
    
    async def unload_model(self, instance_name: str, model_name: str) -> bool:
        """Unload a model to free memory."""
        
        model_key = self._get_model_key(instance_name, model_name)
        
        if model_key in self.models:
            del self.models[model_key]
            del self.model_configs[model_key]
            logger.info(f"Unloaded model {model_name} for instance {instance_name}")
            return True
        
        return False
    
    def clear_cache(self) -> int:
        """Clear the embedding cache and return number of cleared entries."""
        cache_size = len(self.embedding_cache)
        self.embedding_cache.clear()
        logger.info(f"Cleared embedding cache ({cache_size} entries)")
        return cache_size
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about the embedding cache."""
        return {
            'cache_enabled': self.cache_enabled,
            'cache_size': len(self.embedding_cache),
            'max_cache_size': self.max_cache_size,
            'cache_hit_ratio': getattr(self, '_cache_hits', 0) / max(1, getattr(self, '_cache_requests', 1))
        }
    
    async def benchmark_model(
        self, 
        model_name: str, 
        instance_name: str,
        test_texts: Optional[List[str]] = None,
        batch_sizes: List[int] = [1, 8, 16, 32]
    ) -> Dict[str, Any]:
        """Benchmark embedding generation performance for a model."""
        
        if test_texts is None:
            test_texts = [
                "This is a short test sentence.",
                "This is a longer test sentence with more words to evaluate the performance of the embedding model.",
                "Scientific research in artificial intelligence has made significant progress in recent years, particularly in the areas of natural language processing and computer vision.",
                "The quick brown fox jumps over the lazy dog. This pangram contains every letter of the alphabet and is commonly used for testing purposes."
            ]
        
        benchmark_results = {
            'model_name': model_name,
            'instance_name': instance_name,
            'test_text_count': len(test_texts),
            'batch_results': {},
            'model_info': self.get_model_info(model_name)
        }
        
        try:
            # Ensure model is loaded
            if not await self.initialize_model(model_name, instance_name):
                benchmark_results['error'] = "Failed to load model"
                return benchmark_results
            
            # Test different batch sizes
            for batch_size in batch_sizes:
                logger.info(f"Benchmarking {model_name} with batch size {batch_size}")
                
                start_time = datetime.now()
                
                # Generate embeddings
                embeddings = await self.generate_embeddings(
                    texts=test_texts,
                    instance_name=instance_name,
                    model_name=model_name,
                    batch_size=batch_size,
                    show_progress=False
                )
                
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                # Validate embeddings
                validation = await self.validate_embedding_quality(
                    embeddings=embeddings,
                    texts=test_texts,
                    model_name=model_name
                )
                
                benchmark_results['batch_results'][batch_size] = {
                    'duration_seconds': duration,
                    'texts_per_second': len(test_texts) / duration if duration > 0 else 0,
                    'embedding_dimension': len(embeddings[0]) if embeddings else 0,
                    'quality_score': validation.get('quality_score', 0.0),
                    'validation_issues': len(validation.get('issues', [])),
                    'mean_magnitude': validation.get('stats', {}).get('mean_magnitude', 0.0)
                }
            
            # Find optimal batch size
            best_batch_size = max(
                benchmark_results['batch_results'].keys(),
                key=lambda bs: benchmark_results['batch_results'][bs]['texts_per_second']
            )
            
            benchmark_results['recommended_batch_size'] = best_batch_size
            benchmark_results['benchmark_completed'] = True
            
        except Exception as e:
            benchmark_results['error'] = str(e)
            benchmark_results['benchmark_completed'] = False
            logger.error(f"Error benchmarking model {model_name}: {e}")
        
        return benchmark_results
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the embedding service."""
        
        health_status = {
            'status': 'healthy',
            'loaded_models': len(self.models),
            'cache_size': len(self.embedding_cache),
            'supported_models': len(self.supported_models),
            'cuda_available': torch.cuda.is_available(),
            'issues': [],
            'last_check': datetime.now().isoformat()
        }
        
        try:
            # Check if any models are loaded
            if not self.models:
                health_status['issues'].append("No models currently loaded")
                health_status['status'] = 'warning'
            
            # Check model health
            for model_key, model in self.models.items():
                try:
                    # Test model with a simple embedding
                    test_embedding = model.encode(["test"], convert_to_tensor=False)
                    if len(test_embedding) == 0 or len(test_embedding[0]) == 0:
                        health_status['issues'].append(f"Model {model_key} produced empty embedding")
                        health_status['status'] = 'degraded'
                except Exception as e:
                    health_status['issues'].append(f"Model {model_key} failed health check: {str(e)}")
                    health_status['status'] = 'degraded'
            
            # Check cache health
            if self.cache_enabled and len(self.embedding_cache) > self.max_cache_size * 1.1:
                health_status['issues'].append("Embedding cache size exceeded maximum")
                health_status['status'] = 'warning'
            
        except Exception as e:
            health_status['status'] = 'error'
            health_status['issues'].append(f"Health check failed: {str(e)}")
            logger.error(f"Embedding service health check failed: {e}")
        
        return health_status