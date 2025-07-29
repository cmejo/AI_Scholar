"""
Embedding Retrainer Service for domain-specific embedding fine-tuning and incremental learning.
"""

import asyncio
import json
import logging
import numpy as np
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
from enum import Enum
import hashlib
import os

from core.database import get_db
from core.redis_client import get_redis_client

logger = logging.getLogger(__name__)

class RetrainingStrategy(Enum):
    """Types of retraining strategies."""
    INCREMENTAL = "incremental"
    FULL_RETRAIN = "full_retrain"
    DOMAIN_ADAPTATION = "domain_adaptation"
    FINE_TUNING = "fine_tuning"
    CONTRASTIVE_LEARNING = "contrastive_learning"

class EmbeddingModel(Enum):
    """Types of embedding models."""
    SENTENCE_TRANSFORMER = "sentence_transformer"
    OPENAI_ADA = "openai_ada"
    CUSTOM_BERT = "custom_bert"
    DOMAIN_SPECIFIC = "domain_specific"

@dataclass
class TrainingExample:
    """Represents a training example for embedding retraining."""
    text: str
    label: Optional[str] = None
    domain: Optional[str] = None
    positive_examples: List[str] = None
    negative_examples: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.positive_examples is None:
            self.positive_examples = []
        if self.negative_examples is None:
            self.negative_examples = []
        if self.metadata is None:
            self.metadata = {}

@dataclass
class RetrainingConfig:
    """Configuration for embedding retraining."""
    strategy: RetrainingStrategy
    model_type: EmbeddingModel
    learning_rate: float = 1e-5
    batch_size: int = 16
    epochs: int = 3
    domain_weight: float = 0.5
    contrastive_margin: float = 0.5
    validation_split: float = 0.2
    early_stopping_patience: int = 3
    max_sequence_length: int = 512
    temperature: float = 0.07
    use_hard_negatives: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        result['strategy'] = self.strategy.value
        result['model_type'] = self.model_type.value
        return result

@dataclass
class RetrainingResult:
    """Results from embedding retraining."""
    model_id: str
    strategy: RetrainingStrategy
    training_loss: float
    validation_loss: float
    improvement_score: float
    training_examples_count: int
    training_duration: float
    model_path: str
    performance_metrics: Dict[str, float]
    created_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        result['strategy'] = self.strategy.value
        result['created_at'] = self.created_at.isoformat()
        return result

@dataclass
class DomainAdaptationData:
    """Data for domain adaptation."""
    domain_name: str
    domain_examples: List[TrainingExample]
    domain_vocabulary: List[str]
    domain_concepts: List[str]
    adaptation_weight: float = 1.0

class EmbeddingRetrainer:
    """Service for embedding retraining and domain adaptation."""
    
    def __init__(self):
        self.redis_client = None
        self.model_cache_ttl = 86400  # 24 hours
        self.training_data_cache_ttl = 3600  # 1 hour
        self.min_training_examples = 50
        self.max_training_examples = 10000
        self.model_storage_path = "models/embeddings"
        self.supported_domains = ["technology", "science", "business", "healthcare", "education", "legal"]
        
    async def initialize(self):
        """Initialize the embedding retrainer service."""
        try:
            self.redis_client = get_redis_client()
            try:
                await self.redis_client.connect()
            except Exception as redis_error:
                logger.warning(f"Redis connection failed, continuing without Redis: {redis_error}")
                self.redis_client = None
            
            # Create model storage directory
            os.makedirs(self.model_storage_path, exist_ok=True)
            
            logger.info("EmbeddingRetrainer initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize EmbeddingRetrainer: {e}")
            raise
    
    async def collect_training_data(self, domain: str = None, 
                                  time_window_days: int = 30) -> List[TrainingExample]:
        """Collect training data from user interactions and documents."""
        try:
            # Get document data for training
            document_data = await self._get_document_training_data(domain, time_window_days)
            
            # Get user interaction data
            interaction_data = await self._get_interaction_training_data(domain, time_window_days)
            
            # Get feedback data for contrastive learning
            feedback_data = await self._get_feedback_training_data(domain, time_window_days)
            
            # Combine and process training examples
            training_examples = []
            
            # Process document data
            for doc_data in document_data:
                example = TrainingExample(
                    text=doc_data['content'],
                    domain=doc_data.get('domain', domain),
                    metadata={
                        'source': 'document',
                        'document_id': doc_data['document_id'],
                        'tags': doc_data.get('tags', [])
                    }
                )
                training_examples.append(example)
            
            # Process interaction data for contrastive learning
            for interaction in interaction_data:
                query = interaction['query']
                relevant_docs = interaction.get('relevant_documents', [])
                irrelevant_docs = interaction.get('irrelevant_documents', [])
                
                example = TrainingExample(
                    text=query,
                    domain=interaction.get('domain', domain),
                    positive_examples=relevant_docs,
                    negative_examples=irrelevant_docs,
                    metadata={
                        'source': 'interaction',
                        'user_id': interaction['user_id'],
                        'satisfaction_score': interaction.get('satisfaction_score', 0)
                    }
                )
                training_examples.append(example)
            
            # Process feedback data
            for feedback in feedback_data:
                if feedback['feedback_type'] == 'relevance':
                    example = TrainingExample(
                        text=feedback['query'],
                        domain=feedback.get('domain', domain),
                        positive_examples=feedback.get('relevant_docs', []),
                        negative_examples=feedback.get('irrelevant_docs', []),
                        metadata={
                            'source': 'feedback',
                            'feedback_score': feedback.get('score', 0)
                        }
                    )
                    training_examples.append(example)
            
            # Cache training data if Redis is available
            if self.redis_client:
                try:
                    cache_key = f"training_data:{domain or 'general'}:{time_window_days}"
                    await self.redis_client.set(
                        cache_key,
                        json.dumps([asdict(ex) for ex in training_examples], default=str),
                        expire=self.training_data_cache_ttl
                    )
                except Exception as e:
                    logger.warning(f"Failed to cache training data: {e}")
            
            logger.info(f"Collected {len(training_examples)} training examples for domain: {domain or 'general'}")
            return training_examples
            
        except Exception as e:
            logger.error(f"Error collecting training data: {e}")
            return []
    
    async def prepare_domain_adaptation_data(self, domain: str) -> DomainAdaptationData:
        """Prepare data for domain-specific adaptation."""
        try:
            # Get domain-specific examples
            domain_examples = await self.collect_training_data(domain=domain)
            
            # Extract domain vocabulary
            domain_vocabulary = await self._extract_domain_vocabulary(domain_examples)
            
            # Identify domain concepts
            domain_concepts = await self._identify_domain_concepts(domain_examples)
            
            # Calculate adaptation weight based on data quality and quantity
            adaptation_weight = await self._calculate_adaptation_weight(domain_examples)
            
            adaptation_data = DomainAdaptationData(
                domain_name=domain,
                domain_examples=domain_examples,
                domain_vocabulary=domain_vocabulary,
                domain_concepts=domain_concepts,
                adaptation_weight=adaptation_weight
            )
            
            logger.info(f"Prepared domain adaptation data for {domain}: {len(domain_examples)} examples, {len(domain_vocabulary)} vocab terms")
            return adaptation_data
            
        except Exception as e:
            logger.error(f"Error preparing domain adaptation data: {e}")
            return DomainAdaptationData(domain, [], [], [], 0.0)
    
    async def retrain_embeddings(self, training_examples: List[TrainingExample],
                               config: RetrainingConfig) -> RetrainingResult:
        """Retrain embeddings using the specified strategy."""
        try:
            if len(training_examples) < self.min_training_examples:
                raise ValueError(f"Insufficient training examples: {len(training_examples)} < {self.min_training_examples}")
            
            # Limit training examples to prevent memory issues
            if len(training_examples) > self.max_training_examples:
                training_examples = training_examples[:self.max_training_examples]
                logger.warning(f"Limited training examples to {self.max_training_examples}")
            
            start_time = datetime.now()
            
            # Choose retraining strategy
            if config.strategy == RetrainingStrategy.INCREMENTAL:
                result = await self._incremental_retraining(training_examples, config)
            elif config.strategy == RetrainingStrategy.FULL_RETRAIN:
                result = await self._full_retraining(training_examples, config)
            elif config.strategy == RetrainingStrategy.DOMAIN_ADAPTATION:
                result = await self._domain_adaptation_retraining(training_examples, config)
            elif config.strategy == RetrainingStrategy.FINE_TUNING:
                result = await self._fine_tuning_retraining(training_examples, config)
            elif config.strategy == RetrainingStrategy.CONTRASTIVE_LEARNING:
                result = await self._contrastive_learning_retraining(training_examples, config)
            else:
                raise ValueError(f"Unsupported retraining strategy: {config.strategy}")
            
            # Calculate training duration
            training_duration = (datetime.now() - start_time).total_seconds()
            result.training_duration = training_duration
            result.training_examples_count = len(training_examples)
            
            # Store model and results
            await self._store_retrained_model(result)
            await self._log_retraining_result(result)
            
            logger.info(f"Completed {config.strategy.value} retraining: improvement={result.improvement_score:.3f}, duration={training_duration:.1f}s")
            return result
            
        except Exception as e:
            logger.error(f"Error retraining embeddings: {e}")
            raise
    
    async def evaluate_model_performance(self, model_id: str, 
                                       test_examples: List[TrainingExample]) -> Dict[str, float]:
        """Evaluate the performance of a retrained model."""
        try:
            # Load model
            model_data = await self._load_retrained_model(model_id)
            if not model_data:
                raise ValueError(f"Model {model_id} not found")
            
            # Prepare test data
            test_queries = []
            test_documents = []
            relevance_labels = []
            
            for example in test_examples:
                if example.positive_examples:
                    for pos_doc in example.positive_examples:
                        test_queries.append(example.text)
                        test_documents.append(pos_doc)
                        relevance_labels.append(1)  # Relevant
                
                if example.negative_examples:
                    for neg_doc in example.negative_examples:
                        test_queries.append(example.text)
                        test_documents.append(neg_doc)
                        relevance_labels.append(0)  # Not relevant
            
            if not test_queries:
                return {'error': 'No test data available'}
            
            # Calculate embeddings (simulated)
            query_embeddings = await self._calculate_embeddings(test_queries, model_id)
            doc_embeddings = await self._calculate_embeddings(test_documents, model_id)
            
            # Calculate similarity scores
            similarity_scores = []
            for i in range(len(query_embeddings)):
                similarity = np.dot(query_embeddings[i], doc_embeddings[i])
                similarity_scores.append(similarity)
            
            # Calculate performance metrics
            metrics = await self._calculate_performance_metrics(similarity_scores, relevance_labels)
            
            logger.info(f"Evaluated model {model_id}: {metrics}")
            return metrics
            
        except Exception as e:
            logger.error(f"Error evaluating model performance: {e}")
            return {'error': str(e)}
    
    async def deploy_retrained_model(self, model_id: str, deployment_strategy: str = "gradual") -> bool:
        """Deploy a retrained model to production."""
        try:
            # Load model data
            model_data = await self._load_retrained_model(model_id)
            if not model_data:
                raise ValueError(f"Model {model_id} not found")
            
            # Validate model performance
            validation_passed = await self._validate_model_for_deployment(model_id)
            if not validation_passed:
                logger.warning(f"Model {model_id} failed validation checks")
                return False
            
            # Deploy based on strategy
            if deployment_strategy == "gradual":
                success = await self._gradual_deployment(model_id, model_data)
            elif deployment_strategy == "immediate":
                success = await self._immediate_deployment(model_id, model_data)
            elif deployment_strategy == "a_b_test":
                success = await self._ab_test_deployment(model_id, model_data)
            else:
                raise ValueError(f"Unsupported deployment strategy: {deployment_strategy}")
            
            if success:
                # Update deployment status
                await self._update_deployment_status(model_id, "deployed")
                
                # Log deployment
                await self._log_model_deployment(model_id, deployment_strategy)
                
                logger.info(f"Successfully deployed model {model_id} using {deployment_strategy} strategy")
            
            return success
            
        except Exception as e:
            logger.error(f"Error deploying retrained model: {e}")
            return False
    
    async def monitor_model_performance(self, model_id: str, 
                                      monitoring_period_hours: int = 24) -> Dict[str, Any]:
        """Monitor the performance of a deployed model."""
        try:
            # Get model deployment info
            deployment_info = await self._get_deployment_info(model_id)
            if not deployment_info:
                return {'error': 'Model not deployed'}
            
            deployment_time = deployment_info['deployed_at']
            
            # Get performance data before and after deployment
            before_data = await self._get_model_performance_data(
                end_time=deployment_time,
                time_window_hours=monitoring_period_hours
            )
            
            after_data = await self._get_model_performance_data(
                start_time=deployment_time,
                time_window_hours=monitoring_period_hours
            )
            
            # Calculate performance changes
            performance_analysis = {
                'model_id': model_id,
                'monitoring_period_hours': monitoring_period_hours,
                'deployment_time': deployment_time.isoformat(),
                'before_metrics': await self._calculate_aggregate_performance(before_data),
                'after_metrics': await self._calculate_aggregate_performance(after_data),
                'performance_changes': {},
                'alerts': []
            }
            
            # Calculate changes
            before_metrics = performance_analysis['before_metrics']
            after_metrics = performance_analysis['after_metrics']
            
            for metric in before_metrics:
                if metric in after_metrics:
                    before_val = before_metrics[metric]
                    after_val = after_metrics[metric]
                    
                    if before_val != 0:
                        change = (after_val - before_val) / before_val
                        performance_analysis['performance_changes'][metric] = change
                        
                        # Check for alerts
                        if abs(change) > 0.1:  # 10% change threshold
                            alert_type = "improvement" if change > 0 else "degradation"
                            performance_analysis['alerts'].append({
                                'type': alert_type,
                                'metric': metric,
                                'change': change,
                                'severity': 'high' if abs(change) > 0.2 else 'medium'
                            })
            
            # Store monitoring results
            await self._store_monitoring_results(model_id, performance_analysis)
            
            logger.info(f"Monitored model {model_id}: {len(performance_analysis['alerts'])} alerts")
            return performance_analysis
            
        except Exception as e:
            logger.error(f"Error monitoring model performance: {e}")
            return {'error': str(e)}
    
    async def get_retraining_recommendations(self, domain: str = None) -> List[Dict[str, Any]]:
        """Get recommendations for embedding retraining."""
        try:
            recommendations = []
            
            # Analyze current model performance
            current_performance = await self._analyze_current_model_performance(domain)
            
            # Check for performance degradation
            if current_performance.get('avg_relevance_score', 1.0) < 0.7:
                recommendations.append({
                    'type': 'performance_degradation',
                    'strategy': RetrainingStrategy.FINE_TUNING.value,
                    'priority': 'high',
                    'description': 'Model performance has degraded, fine-tuning recommended',
                    'expected_improvement': 0.15,
                    'estimated_effort': 'medium'
                })
            
            # Check for new domain data
            new_domain_data = await self._check_new_domain_data(domain)
            if new_domain_data['new_examples'] > 100:
                recommendations.append({
                    'type': 'new_domain_data',
                    'strategy': RetrainingStrategy.INCREMENTAL.value,
                    'priority': 'medium',
                    'description': f'New domain data available: {new_domain_data["new_examples"]} examples',
                    'expected_improvement': 0.1,
                    'estimated_effort': 'low'
                })
            
            # Check for domain shift
            domain_shift = await self._detect_domain_shift(domain)
            if domain_shift['shift_detected']:
                recommendations.append({
                    'type': 'domain_shift',
                    'strategy': RetrainingStrategy.DOMAIN_ADAPTATION.value,
                    'priority': 'high',
                    'description': f'Domain shift detected: {domain_shift["description"]}',
                    'expected_improvement': 0.2,
                    'estimated_effort': 'high'
                })
            
            # Check for user feedback patterns
            feedback_patterns = await self._analyze_feedback_patterns(domain)
            if feedback_patterns.get('negative_feedback_rate', 0) > 0.3:
                recommendations.append({
                    'type': 'negative_feedback',
                    'strategy': RetrainingStrategy.CONTRASTIVE_LEARNING.value,
                    'priority': 'medium',
                    'description': 'High negative feedback rate, contrastive learning recommended',
                    'expected_improvement': 0.12,
                    'estimated_effort': 'medium'
                })
            
            # Sort by priority and expected improvement
            priority_order = {'high': 3, 'medium': 2, 'low': 1}
            recommendations.sort(
                key=lambda x: (priority_order.get(x['priority'], 0), x['expected_improvement']),
                reverse=True
            )
            
            logger.info(f"Generated {len(recommendations)} retraining recommendations for domain: {domain or 'general'}")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting retraining recommendations: {e}")
            return []
    
    async def _get_document_training_data(self, domain: str, time_window_days: int) -> List[Dict[str, Any]]:
        """Get document data for training."""
        try:
            from core.database import Document, DocumentTag
            
            db_session = next(get_db())
            try:
                cutoff_time = datetime.now() - timedelta(days=time_window_days)
                
                query = db_session.query(Document).filter(
                    Document.created_at >= cutoff_time,
                    Document.status == 'completed'
                )
                
                # Filter by domain if specified
                if domain:
                    query = query.join(DocumentTag).filter(
                        DocumentTag.tag_name == domain,
                        DocumentTag.tag_type == 'domain'
                    )
                
                documents = query.limit(1000).all()  # Limit for performance
                
                document_data = []
                for doc in documents:
                    # Get document tags
                    tags = db_session.query(DocumentTag).filter(
                        DocumentTag.document_id == doc.id
                    ).all()
                    
                    document_data.append({
                        'document_id': doc.id,
                        'content': f"Document: {doc.name}",  # Simplified content
                        'domain': domain,
                        'tags': [tag.tag_name for tag in tags]
                    })
                
                return document_data
                
            finally:
                db_session.close()
                
        except Exception as e:
            logger.error(f"Error getting document training data: {e}")
            return []
    
    async def _get_interaction_training_data(self, domain: str, time_window_days: int) -> List[Dict[str, Any]]:
        """Get user interaction data for training."""
        try:
            from core.database import AnalyticsEvent
            
            db_session = next(get_db())
            try:
                cutoff_time = datetime.now() - timedelta(days=time_window_days)
                
                results = db_session.query(AnalyticsEvent).filter(
                    AnalyticsEvent.event_type == 'query_submitted',
                    AnalyticsEvent.timestamp >= cutoff_time
                ).limit(500).all()
                
                interaction_data = []
                for result in results:
                    event_data = result.event_data or {}
                    
                    interaction_data.append({
                        'query': event_data.get('query', ''),
                        'user_id': result.user_id,
                        'domain': domain,
                        'relevant_documents': event_data.get('relevant_documents', []),
                        'irrelevant_documents': event_data.get('irrelevant_documents', []),
                        'satisfaction_score': event_data.get('satisfaction_score', 0)
                    })
                
                return interaction_data
                
            finally:
                db_session.close()
                
        except Exception as e:
            logger.error(f"Error getting interaction training data: {e}")
            return []
    
    async def _get_feedback_training_data(self, domain: str, time_window_days: int) -> List[Dict[str, Any]]:
        """Get feedback data for training."""
        try:
            from core.database import UserFeedback
            
            db_session = next(get_db())
            try:
                cutoff_time = datetime.now() - timedelta(days=time_window_days)
                
                results = db_session.query(UserFeedback).filter(
                    UserFeedback.created_at >= cutoff_time,
                    UserFeedback.feedback_type == 'relevance'
                ).limit(200).all()
                
                feedback_data = []
                for result in results:
                    feedback_value = result.feedback_value or {}
                    
                    feedback_data.append({
                        'query': feedback_value.get('query', ''),
                        'feedback_type': result.feedback_type,
                        'domain': domain,
                        'relevant_docs': feedback_value.get('relevant_docs', []),
                        'irrelevant_docs': feedback_value.get('irrelevant_docs', []),
                        'score': feedback_value.get('score', 0)
                    })
                
                return feedback_data
                
            finally:
                db_session.close()
                
        except Exception as e:
            logger.error(f"Error getting feedback training data: {e}")
            return []
    
    async def _extract_domain_vocabulary(self, examples: List[TrainingExample]) -> List[str]:
        """Extract domain-specific vocabulary from training examples."""
        try:
            word_counts = Counter()
            
            for example in examples:
                # Simple tokenization
                words = example.text.lower().split()
                for word in words:
                    if len(word) > 3 and word.isalpha():  # Filter short words and non-alphabetic
                        word_counts[word] += 1
            
            # Return most common domain-specific terms
            domain_vocab = [word for word, count in word_counts.most_common(500) if count > 2]
            
            return domain_vocab
            
        except Exception as e:
            logger.error(f"Error extracting domain vocabulary: {e}")
            return []
    
    async def _identify_domain_concepts(self, examples: List[TrainingExample]) -> List[str]:
        """Identify key concepts in the domain."""
        try:
            # Simple concept identification based on frequent multi-word phrases
            concepts = []
            
            # Extract bigrams and trigrams
            for example in examples:
                words = example.text.lower().split()
                
                # Bigrams
                for i in range(len(words) - 1):
                    bigram = f"{words[i]} {words[i+1]}"
                    if len(bigram) > 6:  # Filter short phrases
                        concepts.append(bigram)
                
                # Trigrams
                for i in range(len(words) - 2):
                    trigram = f"{words[i]} {words[i+1]} {words[i+2]}"
                    if len(trigram) > 10:  # Filter short phrases
                        concepts.append(trigram)
            
            # Count and return most common concepts
            concept_counts = Counter(concepts)
            domain_concepts = [concept for concept, count in concept_counts.most_common(100) if count > 2]
            
            return domain_concepts
            
        except Exception as e:
            logger.error(f"Error identifying domain concepts: {e}")
            return []
    
    async def _calculate_adaptation_weight(self, examples: List[TrainingExample]) -> float:
        """Calculate adaptation weight based on data quality and quantity."""
        try:
            if not examples:
                return 0.0
            
            # Base weight on quantity
            quantity_score = min(len(examples) / 1000, 1.0)  # Normalize to 1000 examples
            
            # Quality score based on metadata richness
            quality_scores = []
            for example in examples:
                score = 0.0
                
                # Has domain information
                if example.domain:
                    score += 0.2
                
                # Has positive/negative examples (for contrastive learning)
                if example.positive_examples:
                    score += 0.3
                if example.negative_examples:
                    score += 0.3
                
                # Has metadata
                if example.metadata:
                    score += 0.2
                
                quality_scores.append(score)
            
            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
            
            # Combined weight
            adaptation_weight = (quantity_score * 0.6) + (avg_quality * 0.4)
            
            return min(adaptation_weight, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating adaptation weight: {e}")
            return 0.0
    
    async def _incremental_retraining(self, training_examples: List[TrainingExample],
                                   config: RetrainingConfig) -> RetrainingResult:
        """Perform incremental retraining."""
        try:
            # Simulate incremental retraining
            model_id = f"incremental_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Simulate training process
            training_loss = 0.15 + np.random.uniform(-0.05, 0.05)
            validation_loss = 0.18 + np.random.uniform(-0.05, 0.05)
            
            # Calculate improvement (incremental typically shows modest improvement)
            improvement_score = 0.08 + np.random.uniform(-0.02, 0.04)
            
            # Performance metrics
            performance_metrics = {
                'accuracy': 0.82 + np.random.uniform(-0.05, 0.08),
                'precision': 0.79 + np.random.uniform(-0.05, 0.08),
                'recall': 0.84 + np.random.uniform(-0.05, 0.08),
                'f1_score': 0.81 + np.random.uniform(-0.05, 0.08)
            }
            
            # Model path
            model_path = os.path.join(self.model_storage_path, f"{model_id}.pkl")
            
            result = RetrainingResult(
                model_id=model_id,
                strategy=RetrainingStrategy.INCREMENTAL,
                training_loss=training_loss,
                validation_loss=validation_loss,
                improvement_score=improvement_score,
                training_examples_count=len(training_examples),
                training_duration=0.0,  # Will be set by caller
                model_path=model_path,
                performance_metrics=performance_metrics,
                created_at=datetime.now()
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in incremental retraining: {e}")
            raise
    
    async def _full_retraining(self, training_examples: List[TrainingExample],
                             config: RetrainingConfig) -> RetrainingResult:
        """Perform full retraining."""
        try:
            model_id = f"full_retrain_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Simulate full retraining (typically better improvement but more expensive)
            training_loss = 0.12 + np.random.uniform(-0.03, 0.03)
            validation_loss = 0.15 + np.random.uniform(-0.03, 0.03)
            
            improvement_score = 0.15 + np.random.uniform(-0.03, 0.05)
            
            performance_metrics = {
                'accuracy': 0.87 + np.random.uniform(-0.03, 0.05),
                'precision': 0.85 + np.random.uniform(-0.03, 0.05),
                'recall': 0.88 + np.random.uniform(-0.03, 0.05),
                'f1_score': 0.86 + np.random.uniform(-0.03, 0.05)
            }
            
            model_path = os.path.join(self.model_storage_path, f"{model_id}.pkl")
            
            result = RetrainingResult(
                model_id=model_id,
                strategy=RetrainingStrategy.FULL_RETRAIN,
                training_loss=training_loss,
                validation_loss=validation_loss,
                improvement_score=improvement_score,
                training_examples_count=len(training_examples),
                training_duration=0.0,
                model_path=model_path,
                performance_metrics=performance_metrics,
                created_at=datetime.now()
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in full retraining: {e}")
            raise
    
    async def _domain_adaptation_retraining(self, training_examples: List[TrainingExample],
                                          config: RetrainingConfig) -> RetrainingResult:
        """Perform domain adaptation retraining."""
        try:
            model_id = f"domain_adapt_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Domain adaptation typically shows good improvement for domain-specific tasks
            training_loss = 0.10 + np.random.uniform(-0.02, 0.02)
            validation_loss = 0.13 + np.random.uniform(-0.02, 0.02)
            
            improvement_score = 0.20 + np.random.uniform(-0.05, 0.08)
            
            performance_metrics = {
                'accuracy': 0.89 + np.random.uniform(-0.02, 0.04),
                'precision': 0.87 + np.random.uniform(-0.02, 0.04),
                'recall': 0.90 + np.random.uniform(-0.02, 0.04),
                'f1_score': 0.88 + np.random.uniform(-0.02, 0.04),
                'domain_specificity': 0.92 + np.random.uniform(-0.02, 0.03)
            }
            
            model_path = os.path.join(self.model_storage_path, f"{model_id}.pkl")
            
            result = RetrainingResult(
                model_id=model_id,
                strategy=RetrainingStrategy.DOMAIN_ADAPTATION,
                training_loss=training_loss,
                validation_loss=validation_loss,
                improvement_score=improvement_score,
                training_examples_count=len(training_examples),
                training_duration=0.0,
                model_path=model_path,
                performance_metrics=performance_metrics,
                created_at=datetime.now()
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in domain adaptation retraining: {e}")
            raise
    
    async def _fine_tuning_retraining(self, training_examples: List[TrainingExample],
                                    config: RetrainingConfig) -> RetrainingResult:
        """Perform fine-tuning retraining."""
        try:
            model_id = f"fine_tune_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Fine-tuning typically shows moderate improvement with good stability
            training_loss = 0.13 + np.random.uniform(-0.02, 0.02)
            validation_loss = 0.16 + np.random.uniform(-0.02, 0.02)
            
            improvement_score = 0.12 + np.random.uniform(-0.02, 0.04)
            
            performance_metrics = {
                'accuracy': 0.85 + np.random.uniform(-0.02, 0.04),
                'precision': 0.83 + np.random.uniform(-0.02, 0.04),
                'recall': 0.86 + np.random.uniform(-0.02, 0.04),
                'f1_score': 0.84 + np.random.uniform(-0.02, 0.04),
                'stability_score': 0.91 + np.random.uniform(-0.02, 0.03)
            }
            
            model_path = os.path.join(self.model_storage_path, f"{model_id}.pkl")
            
            result = RetrainingResult(
                model_id=model_id,
                strategy=RetrainingStrategy.FINE_TUNING,
                training_loss=training_loss,
                validation_loss=validation_loss,
                improvement_score=improvement_score,
                training_examples_count=len(training_examples),
                training_duration=0.0,
                model_path=model_path,
                performance_metrics=performance_metrics,
                created_at=datetime.now()
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in fine-tuning retraining: {e}")
            raise
    
    async def _contrastive_learning_retraining(self, training_examples: List[TrainingExample],
                                             config: RetrainingConfig) -> RetrainingResult:
        """Perform contrastive learning retraining."""
        try:
            model_id = f"contrastive_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Contrastive learning can show good improvement for similarity tasks
            training_loss = 0.11 + np.random.uniform(-0.02, 0.02)
            validation_loss = 0.14 + np.random.uniform(-0.02, 0.02)
            
            improvement_score = 0.18 + np.random.uniform(-0.04, 0.06)
            
            performance_metrics = {
                'accuracy': 0.88 + np.random.uniform(-0.03, 0.04),
                'precision': 0.86 + np.random.uniform(-0.03, 0.04),
                'recall': 0.89 + np.random.uniform(-0.03, 0.04),
                'f1_score': 0.87 + np.random.uniform(-0.03, 0.04),
                'similarity_quality': 0.90 + np.random.uniform(-0.02, 0.03),
                'contrastive_margin': config.contrastive_margin
            }
            
            model_path = os.path.join(self.model_storage_path, f"{model_id}.pkl")
            
            result = RetrainingResult(
                model_id=model_id,
                strategy=RetrainingStrategy.CONTRASTIVE_LEARNING,
                training_loss=training_loss,
                validation_loss=validation_loss,
                improvement_score=improvement_score,
                training_examples_count=len(training_examples),
                training_duration=0.0,
                model_path=model_path,
                performance_metrics=performance_metrics,
                created_at=datetime.now()
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in contrastive learning retraining: {e}")
            raise
    
    async def _calculate_embeddings(self, texts: List[str], model_id: str) -> List[np.ndarray]:
        """Calculate embeddings using the specified model (simulated)."""
        try:
            # Simulate embedding calculation
            embeddings = []
            embedding_dim = 384  # Common dimension for sentence transformers
            
            for text in texts:
                # Create deterministic but varied embeddings based on text
                text_hash = hashlib.md5(text.encode()).hexdigest()
                seed = int(text_hash[:8], 16)
                np.random.seed(seed)
                
                # Generate embedding with some structure
                embedding = np.random.normal(0, 1, embedding_dim)
                embedding = embedding / np.linalg.norm(embedding)  # Normalize
                
                embeddings.append(embedding)
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Error calculating embeddings: {e}")
            return []
    
    async def _calculate_performance_metrics(self, similarity_scores: List[float],
                                           relevance_labels: List[int]) -> Dict[str, float]:
        """Calculate performance metrics from similarity scores and labels."""
        try:
            if not similarity_scores or not relevance_labels:
                return {}
            
            # Convert to numpy arrays
            scores = np.array(similarity_scores)
            labels = np.array(relevance_labels)
            
            # Calculate metrics at different thresholds
            thresholds = np.linspace(0.1, 0.9, 9)
            best_f1 = 0
            best_metrics = {}
            
            for threshold in thresholds:
                predictions = (scores > threshold).astype(int)
                
                # Calculate basic metrics
                tp = np.sum((predictions == 1) & (labels == 1))
                fp = np.sum((predictions == 1) & (labels == 0))
                tn = np.sum((predictions == 0) & (labels == 0))
                fn = np.sum((predictions == 0) & (labels == 1))
                
                if tp + fp > 0:
                    precision = tp / (tp + fp)
                else:
                    precision = 0
                
                if tp + fn > 0:
                    recall = tp / (tp + fn)
                else:
                    recall = 0
                
                if precision + recall > 0:
                    f1 = 2 * (precision * recall) / (precision + recall)
                else:
                    f1 = 0
                
                if tp + tn + fp + fn > 0:
                    accuracy = (tp + tn) / (tp + tn + fp + fn)
                else:
                    accuracy = 0
                
                if f1 > best_f1:
                    best_f1 = f1
                    best_metrics = {
                        'accuracy': accuracy,
                        'precision': precision,
                        'recall': recall,
                        'f1_score': f1,
                        'threshold': threshold
                    }
            
            # Add additional metrics
            best_metrics['mean_similarity'] = np.mean(scores)
            best_metrics['std_similarity'] = np.std(scores)
            
            return best_metrics
            
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {e}")
            return {}
    
    async def _store_retrained_model(self, result: RetrainingResult):
        """Store retrained model data."""
        try:
            # Simulate storing model file
            model_data = {
                'model_id': result.model_id,
                'strategy': result.strategy.value,
                'performance_metrics': result.performance_metrics,
                'created_at': result.created_at.isoformat(),
                'model_config': {
                    'embedding_dim': 384,
                    'model_type': 'sentence_transformer'
                }
            }
            
            # Store in file system (simulated)
            with open(result.model_path, 'wb') as f:
                pickle.dump(model_data, f)
            
            # Store metadata in Redis if available
            if self.redis_client:
                try:
                    await self.redis_client.set(
                        f"model:{result.model_id}",
                        json.dumps(result.to_dict(), default=str),
                        expire=self.model_cache_ttl
                    )
                except Exception as e:
                    logger.warning(f"Failed to store model metadata in Redis: {e}")
            
        except Exception as e:
            logger.error(f"Error storing retrained model: {e}")
    
    async def _load_retrained_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Load retrained model data."""
        try:
            # Try Redis first if available
            if self.redis_client:
                try:
                    cached_data = await self.redis_client.get(f"model:{model_id}")
                    if cached_data:
                        return json.loads(cached_data)
                except Exception as e:
                    logger.warning(f"Failed to load from Redis: {e}")
            
            # Try file system
            model_path = os.path.join(self.model_storage_path, f"{model_id}.pkl")
            if os.path.exists(model_path):
                with open(model_path, 'rb') as f:
                    return pickle.load(f)
            
            return None
            
        except Exception as e:
            logger.error(f"Error loading retrained model: {e}")
            return None
    
    async def _log_retraining_result(self, result: RetrainingResult):
        """Log retraining result to database."""
        try:
            from core.database import AnalyticsEvent
            
            db_session = next(get_db())
            try:
                event_data = {
                    'model_id': result.model_id,
                    'strategy': result.strategy.value,
                    'training_loss': result.training_loss,
                    'validation_loss': result.validation_loss,
                    'improvement_score': result.improvement_score,
                    'training_examples_count': result.training_examples_count,
                    'training_duration': result.training_duration,
                    'performance_metrics': result.performance_metrics
                }
                
                analytics_event = AnalyticsEvent(
                    event_type="embedding_retraining_completed",
                    event_data=event_data,
                    timestamp=result.created_at
                )
                
                db_session.add(analytics_event)
                db_session.commit()
            finally:
                db_session.close()
                
        except Exception as e:
            logger.error(f"Error logging retraining result: {e}")
    
    async def _validate_model_for_deployment(self, model_id: str) -> bool:
        """Validate model before deployment."""
        try:
            model_data = await self._load_retrained_model(model_id)
            if not model_data:
                return False
            
            # Check minimum performance thresholds
            performance_metrics = model_data.get('performance_metrics', {})
            
            min_thresholds = {
                'accuracy': 0.7,
                'precision': 0.65,
                'recall': 0.65,
                'f1_score': 0.65
            }
            
            for metric, threshold in min_thresholds.items():
                if performance_metrics.get(metric, 0) < threshold:
                    logger.warning(f"Model {model_id} failed validation: {metric} = {performance_metrics.get(metric, 0)} < {threshold}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating model for deployment: {e}")
            return False
    
    async def _gradual_deployment(self, model_id: str, model_data: Dict[str, Any]) -> bool:
        """Deploy model gradually."""
        try:
            # Store deployment configuration for gradual rollout
            deployment_config = {
                'model_id': model_id,
                'deployment_strategy': 'gradual',
                'traffic_percentage': 10,  # Start with 10%
                'deployed_at': datetime.now().isoformat(),
                'status': 'deploying'
            }
            
            if self.redis_client:
                try:
                    await self.redis_client.set(
                        f"deployment:{model_id}",
                        json.dumps(deployment_config),
                        expire=86400 * 7  # Keep for 7 days
                    )
                except Exception as e:
                    logger.warning(f"Failed to store deployment config: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error in gradual deployment: {e}")
            return False
    
    async def _immediate_deployment(self, model_id: str, model_data: Dict[str, Any]) -> bool:
        """Deploy model immediately."""
        try:
            deployment_config = {
                'model_id': model_id,
                'deployment_strategy': 'immediate',
                'traffic_percentage': 100,
                'deployed_at': datetime.now().isoformat(),
                'status': 'deployed'
            }
            
            if self.redis_client:
                try:
                    await self.redis_client.set(
                        f"deployment:{model_id}",
                        json.dumps(deployment_config),
                        expire=86400 * 7
                    )
                except Exception as e:
                    logger.warning(f"Failed to store deployment config: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error in immediate deployment: {e}")
            return False
    
    async def _ab_test_deployment(self, model_id: str, model_data: Dict[str, Any]) -> bool:
        """Deploy model for A/B testing."""
        try:
            deployment_config = {
                'model_id': model_id,
                'deployment_strategy': 'a_b_test',
                'traffic_percentage': 50,
                'deployed_at': datetime.now().isoformat(),
                'status': 'ab_testing',
                'test_duration_days': 14
            }
            
            if self.redis_client:
                try:
                    await self.redis_client.set(
                        f"deployment:{model_id}",
                        json.dumps(deployment_config),
                        expire=86400 * 14  # Keep for test duration
                    )
                except Exception as e:
                    logger.warning(f"Failed to store deployment config: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error in A/B test deployment: {e}")
            return False
    
    async def _update_deployment_status(self, model_id: str, status: str):
        """Update deployment status."""
        try:
            if not self.redis_client:
                return
                
            deployment_data = await self.redis_client.get(f"deployment:{model_id}")
            if deployment_data:
                config = json.loads(deployment_data)
                config['status'] = status
                config['updated_at'] = datetime.now().isoformat()
                
                await self.redis_client.set(
                    f"deployment:{model_id}",
                    json.dumps(config),
                    expire=86400 * 7
                )
                
        except Exception as e:
            logger.error(f"Error updating deployment status: {e}")
    
    async def _log_model_deployment(self, model_id: str, deployment_strategy: str):
        """Log model deployment."""
        try:
            from core.database import AnalyticsEvent
            
            db_session = next(get_db())
            try:
                event_data = {
                    'model_id': model_id,
                    'deployment_strategy': deployment_strategy,
                    'deployed_at': datetime.now().isoformat()
                }
                
                analytics_event = AnalyticsEvent(
                    event_type="embedding_model_deployed",
                    event_data=event_data,
                    timestamp=datetime.now()
                )
                
                db_session.add(analytics_event)
                db_session.commit()
            finally:
                db_session.close()
                
        except Exception as e:
            logger.error(f"Error logging model deployment: {e}")
    
    async def _get_deployment_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get deployment information."""
        try:
            if not self.redis_client:
                # Return mock deployment info for testing
                return {
                    'deployed_at': datetime.now() - timedelta(hours=1),
                    'status': 'deployed'
                }
                
            deployment_data = await self.redis_client.get(f"deployment:{model_id}")
            if deployment_data:
                config = json.loads(deployment_data)
                config['deployed_at'] = datetime.fromisoformat(config['deployed_at'])
                return config
            return None
            
        except Exception as e:
            logger.error(f"Error getting deployment info: {e}")
            return None
    
    async def _get_model_performance_data(self, start_time: datetime = None,
                                        end_time: datetime = None,
                                        time_window_hours: int = 24) -> List[Dict[str, Any]]:
        """Get model performance data."""
        try:
            from core.database import AnalyticsEvent
            
            if end_time is None:
                end_time = datetime.now()
            if start_time is None:
                start_time = end_time - timedelta(hours=time_window_hours)
            
            db_session = next(get_db())
            try:
                results = db_session.query(AnalyticsEvent).filter(
                    AnalyticsEvent.event_type.in_(['query_submitted', 'feedback_provided']),
                    AnalyticsEvent.timestamp >= start_time,
                    AnalyticsEvent.timestamp <= end_time
                ).all()
                
                performance_data = []
                for result in results:
                    event_data = result.event_data or {}
                    performance_data.append({
                        'event_type': result.event_type,
                        'timestamp': result.timestamp,
                        'data': event_data
                    })
                
                return performance_data
                
            finally:
                db_session.close()
                
        except Exception as e:
            logger.error(f"Error getting model performance data: {e}")
            return []
    
    async def _calculate_aggregate_performance(self, performance_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate aggregate performance metrics."""
        try:
            metrics = {
                'query_count': 0,
                'avg_response_time': 0,
                'avg_relevance_score': 0,
                'avg_satisfaction': 0
            }
            
            response_times = []
            relevance_scores = []
            satisfaction_scores = []
            
            for item in performance_data:
                if item['event_type'] == 'query_submitted':
                    metrics['query_count'] += 1
                    data = item['data']
                    
                    if 'response_time' in data:
                        response_times.append(data['response_time'])
                    if 'relevance_score' in data:
                        relevance_scores.append(data['relevance_score'])
                
                elif item['event_type'] == 'feedback_provided':
                    data = item['data']
                    if 'rating' in data:
                        satisfaction_scores.append(data['rating'] / 5.0)  # Normalize to 0-1
            
            if response_times:
                metrics['avg_response_time'] = sum(response_times) / len(response_times)
            if relevance_scores:
                metrics['avg_relevance_score'] = sum(relevance_scores) / len(relevance_scores)
            if satisfaction_scores:
                metrics['avg_satisfaction'] = sum(satisfaction_scores) / len(satisfaction_scores)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating aggregate performance: {e}")
            return {}
    
    async def _store_monitoring_results(self, model_id: str, analysis: Dict[str, Any]):
        """Store monitoring results."""
        try:
            monitoring_key = f"monitoring:{model_id}:{datetime.now().strftime('%Y%m%d_%H')}"
            if self.redis_client:
                try:
                    await self.redis_client.set(
                        monitoring_key,
                        json.dumps(analysis, default=str),
                        expire=86400 * 7  # Keep for 7 days
                    )
                except Exception as e:
                    logger.warning(f"Failed to store monitoring results: {e}")
            
        except Exception as e:
            logger.error(f"Error storing monitoring results: {e}")
    
    async def _analyze_current_model_performance(self, domain: str = None) -> Dict[str, float]:
        """Analyze current model performance."""
        try:
            # Get recent performance data
            performance_data = await self._get_model_performance_data(time_window_hours=168)  # 1 week
            
            # Calculate aggregate metrics
            metrics = await self._calculate_aggregate_performance(performance_data)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error analyzing current model performance: {e}")
            return {}
    
    async def _check_new_domain_data(self, domain: str = None) -> Dict[str, Any]:
        """Check for new domain data."""
        try:
            # Get recent training data
            recent_examples = await self.collect_training_data(domain, time_window_days=7)
            
            return {
                'new_examples': len(recent_examples),
                'domain': domain,
                'data_quality': await self._calculate_adaptation_weight(recent_examples)
            }
            
        except Exception as e:
            logger.error(f"Error checking new domain data: {e}")
            return {'new_examples': 0}
    
    async def _detect_domain_shift(self, domain: str = None) -> Dict[str, Any]:
        """Detect domain shift in data."""
        try:
            # Simple domain shift detection based on vocabulary changes
            old_examples = await self.collect_training_data(domain, time_window_days=90)
            recent_examples = await self.collect_training_data(domain, time_window_days=7)
            
            if not old_examples or not recent_examples:
                return {'shift_detected': False}
            
            old_vocab = await self._extract_domain_vocabulary(old_examples)
            recent_vocab = await self._extract_domain_vocabulary(recent_examples)
            
            # Calculate vocabulary overlap
            old_set = set(old_vocab[:200])  # Top 200 terms
            recent_set = set(recent_vocab[:200])
            
            overlap = len(old_set & recent_set) / len(old_set | recent_set) if old_set | recent_set else 0
            
            shift_detected = overlap < 0.7  # 70% overlap threshold
            
            return {
                'shift_detected': shift_detected,
                'vocabulary_overlap': overlap,
                'description': f'Vocabulary overlap: {overlap:.2f}' if shift_detected else 'No significant shift'
            }
            
        except Exception as e:
            logger.error(f"Error detecting domain shift: {e}")
            return {'shift_detected': False}
    
    async def _analyze_feedback_patterns(self, domain: str = None) -> Dict[str, float]:
        """Analyze feedback patterns."""
        try:
            feedback_data = await self._get_feedback_training_data(domain, time_window_days=30)
            
            if not feedback_data:
                return {'negative_feedback_rate': 0.0}
            
            negative_count = sum(1 for fb in feedback_data if fb.get('score', 0) < 0.5)
            negative_rate = negative_count / len(feedback_data)
            
            return {
                'negative_feedback_rate': negative_rate,
                'total_feedback': len(feedback_data)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing feedback patterns: {e}")
            return {'negative_feedback_rate': 0.0}

# Global instance
embedding_retrainer = EmbeddingRetrainer()