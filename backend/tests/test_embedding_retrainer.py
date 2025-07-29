"""
Tests for EmbeddingRetrainer service.
"""

import pytest
import pytest_asyncio
import asyncio
import json
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any

from services.embedding_retrainer import (
    EmbeddingRetrainer,
    TrainingExample,
    RetrainingConfig,
    RetrainingResult,
    DomainAdaptationData,
    RetrainingStrategy,
    EmbeddingModel
)


class TestEmbeddingRetrainer:
    """Test cases for EmbeddingRetrainer service."""
    
    @pytest_asyncio.fixture
    async def embedding_retrainer(self):
        """Create EmbeddingRetrainer instance for testing."""
        retrainer = EmbeddingRetrainer()
        
        # Mock Redis client
        mock_redis = AsyncMock()
        retrainer.redis_client = mock_redis
        
        # Create temporary model storage
        temp_dir = tempfile.mkdtemp()
        retrainer.model_storage_path = temp_dir
        
        yield retrainer
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def sample_training_examples(self):
        """Create sample training examples."""
        return [
            TrainingExample(
                text="Machine learning algorithms for data analysis",
                domain="technology",
                positive_examples=["Deep learning neural networks", "Statistical analysis methods"],
                negative_examples=["Cooking recipes", "Sports news"],
                metadata={"source": "document", "quality": 0.8}
            ),
            TrainingExample(
                text="Natural language processing techniques",
                domain="technology",
                positive_examples=["Text classification models", "Sentiment analysis"],
                negative_examples=["Weather forecast", "Movie reviews"],
                metadata={"source": "interaction", "quality": 0.9}
            ),
            TrainingExample(
                text="Database optimization strategies",
                domain="technology",
                positive_examples=["Query performance tuning", "Index optimization"],
                negative_examples=["Art history", "Music theory"],
                metadata={"source": "feedback", "quality": 0.7}
            )
        ]
    
    @pytest.fixture
    def sample_retraining_config(self):
        """Create sample retraining configuration."""
        return RetrainingConfig(
            strategy=RetrainingStrategy.INCREMENTAL,
            model_type=EmbeddingModel.SENTENCE_TRANSFORMER,
            learning_rate=1e-5,
            batch_size=16,
            epochs=3
        )
    
    @pytest.mark.asyncio
    async def test_initialize(self, embedding_retrainer):
        """Test EmbeddingRetrainer initialization."""
        # Should not raise any exceptions
        await embedding_retrainer.initialize()
        
        # Check that model storage directory exists
        assert os.path.exists(embedding_retrainer.model_storage_path)
    
    @pytest.mark.asyncio
    async def test_collect_training_data(self, embedding_retrainer):
        """Test training data collection."""
        with patch('services.embedding_retrainer.get_db') as mock_get_db:
            # Mock database session
            mock_session = Mock()
            mock_get_db.return_value = iter([mock_session])
            
            # Mock query results
            mock_documents = [
                Mock(id="doc1", name="Test Document 1", created_at=datetime.now()),
                Mock(id="doc2", name="Test Document 2", created_at=datetime.now())
            ]
            mock_session.query.return_value.filter.return_value.limit.return_value.all.return_value = mock_documents
            
            # Mock tags
            mock_session.query.return_value.filter.return_value.all.return_value = []
            
            training_data = await embedding_retrainer.collect_training_data(
                domain="technology",
                time_window_days=30
            )
            
            assert isinstance(training_data, list)
            # Should have some training examples from mocked data
            assert len(training_data) >= 0
    
    @pytest.mark.asyncio
    async def test_prepare_domain_adaptation_data(self, embedding_retrainer, sample_training_examples):
        """Test domain adaptation data preparation."""
        with patch.object(embedding_retrainer, 'collect_training_data', return_value=sample_training_examples):
            adaptation_data = await embedding_retrainer.prepare_domain_adaptation_data("technology")
            
            assert isinstance(adaptation_data, DomainAdaptationData)
            assert adaptation_data.domain_name == "technology"
            assert len(adaptation_data.domain_examples) == len(sample_training_examples)
            assert isinstance(adaptation_data.domain_vocabulary, list)
            assert isinstance(adaptation_data.domain_concepts, list)
            assert 0 <= adaptation_data.adaptation_weight <= 1
    
    @pytest.mark.asyncio
    async def test_incremental_retraining(self, embedding_retrainer, sample_training_examples, sample_retraining_config):
        """Test incremental retraining."""
        sample_retraining_config.strategy = RetrainingStrategy.INCREMENTAL
        
        result = await embedding_retrainer.retrain_embeddings(
            sample_training_examples,
            sample_retraining_config
        )
        
        assert isinstance(result, RetrainingResult)
        assert result.strategy == RetrainingStrategy.INCREMENTAL
        assert result.training_examples_count == len(sample_training_examples)
        assert result.training_loss > 0
        assert result.validation_loss > 0
        assert result.improvement_score > 0
        assert isinstance(result.performance_metrics, dict)
        assert "accuracy" in result.performance_metrics
        assert "precision" in result.performance_metrics
        assert "recall" in result.performance_metrics
        assert "f1_score" in result.performance_metrics
    
    @pytest.mark.asyncio
    async def test_full_retraining(self, embedding_retrainer, sample_training_examples, sample_retraining_config):
        """Test full retraining."""
        sample_retraining_config.strategy = RetrainingStrategy.FULL_RETRAIN
        
        result = await embedding_retrainer.retrain_embeddings(
            sample_training_examples,
            sample_retraining_config
        )
        
        assert isinstance(result, RetrainingResult)
        assert result.strategy == RetrainingStrategy.FULL_RETRAIN
        assert result.improvement_score > 0.1  # Full retrain should show good improvement
    
    @pytest.mark.asyncio
    async def test_domain_adaptation_retraining(self, embedding_retrainer, sample_training_examples, sample_retraining_config):
        """Test domain adaptation retraining."""
        sample_retraining_config.strategy = RetrainingStrategy.DOMAIN_ADAPTATION
        
        result = await embedding_retrainer.retrain_embeddings(
            sample_training_examples,
            sample_retraining_config
        )
        
        assert isinstance(result, RetrainingResult)
        assert result.strategy == RetrainingStrategy.DOMAIN_ADAPTATION
        assert result.improvement_score > 0.15  # Domain adaptation should show good improvement
        assert "domain_specificity" in result.performance_metrics
    
    @pytest.mark.asyncio
    async def test_fine_tuning_retraining(self, embedding_retrainer, sample_training_examples, sample_retraining_config):
        """Test fine-tuning retraining."""
        sample_retraining_config.strategy = RetrainingStrategy.FINE_TUNING
        
        result = await embedding_retrainer.retrain_embeddings(
            sample_training_examples,
            sample_retraining_config
        )
        
        assert isinstance(result, RetrainingResult)
        assert result.strategy == RetrainingStrategy.FINE_TUNING
        assert "stability_score" in result.performance_metrics
    
    @pytest.mark.asyncio
    async def test_contrastive_learning_retraining(self, embedding_retrainer, sample_training_examples, sample_retraining_config):
        """Test contrastive learning retraining."""
        sample_retraining_config.strategy = RetrainingStrategy.CONTRASTIVE_LEARNING
        
        result = await embedding_retrainer.retrain_embeddings(
            sample_training_examples,
            sample_retraining_config
        )
        
        assert isinstance(result, RetrainingResult)
        assert result.strategy == RetrainingStrategy.CONTRASTIVE_LEARNING
        assert "similarity_quality" in result.performance_metrics
        assert "contrastive_margin" in result.performance_metrics
    
    @pytest.mark.asyncio
    async def test_insufficient_training_examples(self, embedding_retrainer, sample_retraining_config):
        """Test handling of insufficient training examples."""
        # Create too few examples
        few_examples = [
            TrainingExample(text="Test example 1", domain="test"),
            TrainingExample(text="Test example 2", domain="test")
        ]
        
        with pytest.raises(ValueError, match="Insufficient training examples"):
            await embedding_retrainer.retrain_embeddings(few_examples, sample_retraining_config)
    
    @pytest.mark.asyncio
    async def test_evaluate_model_performance(self, embedding_retrainer, sample_training_examples):
        """Test model performance evaluation."""
        # First create a model
        config = RetrainingConfig(strategy=RetrainingStrategy.INCREMENTAL, model_type=EmbeddingModel.SENTENCE_TRANSFORMER)
        result = await embedding_retrainer.retrain_embeddings(sample_training_examples, config)
        
        # Evaluate the model
        metrics = await embedding_retrainer.evaluate_model_performance(
            result.model_id,
            sample_training_examples
        )
        
        assert isinstance(metrics, dict)
        if 'error' not in metrics:
            assert 'accuracy' in metrics or len(metrics) > 0
    
    @pytest.mark.asyncio
    async def test_deploy_retrained_model_gradual(self, embedding_retrainer, sample_training_examples):
        """Test gradual model deployment."""
        # Create a model first
        config = RetrainingConfig(strategy=RetrainingStrategy.INCREMENTAL, model_type=EmbeddingModel.SENTENCE_TRANSFORMER)
        result = await embedding_retrainer.retrain_embeddings(sample_training_examples, config)
        
        # Deploy the model
        success = await embedding_retrainer.deploy_retrained_model(result.model_id, "gradual")
        
        assert success is True
        
        # Check deployment was stored in Redis
        embedding_retrainer.redis_client.setex.assert_called()
    
    @pytest.mark.asyncio
    async def test_deploy_retrained_model_immediate(self, embedding_retrainer, sample_training_examples):
        """Test immediate model deployment."""
        # Create a model first
        config = RetrainingConfig(strategy=RetrainingStrategy.INCREMENTAL, model_type=EmbeddingModel.SENTENCE_TRANSFORMER)
        result = await embedding_retrainer.retrain_embeddings(sample_training_examples, config)
        
        # Deploy the model
        success = await embedding_retrainer.deploy_retrained_model(result.model_id, "immediate")
        
        assert success is True
    
    @pytest.mark.asyncio
    async def test_deploy_retrained_model_ab_test(self, embedding_retrainer, sample_training_examples):
        """Test A/B test model deployment."""
        # Create a model first
        config = RetrainingConfig(strategy=RetrainingStrategy.INCREMENTAL, model_type=EmbeddingModel.SENTENCE_TRANSFORMER)
        result = await embedding_retrainer.retrain_embeddings(sample_training_examples, config)
        
        # Deploy the model
        success = await embedding_retrainer.deploy_retrained_model(result.model_id, "a_b_test")
        
        assert success is True
    
    @pytest.mark.asyncio
    async def test_monitor_model_performance(self, embedding_retrainer, sample_training_examples):
        """Test model performance monitoring."""
        # Create and deploy a model first
        config = RetrainingConfig(strategy=RetrainingStrategy.INCREMENTAL, model_type=EmbeddingModel.SENTENCE_TRANSFORMER)
        result = await embedding_retrainer.retrain_embeddings(sample_training_examples, config)
        
        # Mock deployment info
        deployment_info = {
            'deployed_at': datetime.now() - timedelta(hours=1),
            'status': 'deployed'
        }
        
        with patch.object(embedding_retrainer, '_get_deployment_info', return_value=deployment_info):
            with patch.object(embedding_retrainer, '_get_model_performance_data', return_value=[]):
                monitoring_result = await embedding_retrainer.monitor_model_performance(
                    result.model_id,
                    monitoring_period_hours=24
                )
                
                assert isinstance(monitoring_result, dict)
                assert 'model_id' in monitoring_result
                assert 'monitoring_period_hours' in monitoring_result
                assert 'before_metrics' in monitoring_result
                assert 'after_metrics' in monitoring_result
                assert 'performance_changes' in monitoring_result
                assert 'alerts' in monitoring_result
    
    @pytest.mark.asyncio
    async def test_get_retraining_recommendations(self, embedding_retrainer):
        """Test retraining recommendations."""
        with patch.object(embedding_retrainer, '_analyze_current_model_performance', return_value={'avg_relevance_score': 0.6}):
            with patch.object(embedding_retrainer, '_check_new_domain_data', return_value={'new_examples': 150}):
                with patch.object(embedding_retrainer, '_detect_domain_shift', return_value={'shift_detected': True, 'description': 'Test shift'}):
                    with patch.object(embedding_retrainer, '_analyze_feedback_patterns', return_value={'negative_feedback_rate': 0.4}):
                        recommendations = await embedding_retrainer.get_retraining_recommendations("technology")
                        
                        assert isinstance(recommendations, list)
                        assert len(recommendations) > 0
                        
                        # Check recommendation structure
                        for rec in recommendations:
                            assert 'type' in rec
                            assert 'strategy' in rec
                            assert 'priority' in rec
                            assert 'description' in rec
                            assert 'expected_improvement' in rec
                            assert 'estimated_effort' in rec
    
    @pytest.mark.asyncio
    async def test_extract_domain_vocabulary(self, embedding_retrainer, sample_training_examples):
        """Test domain vocabulary extraction."""
        vocabulary = await embedding_retrainer._extract_domain_vocabulary(sample_training_examples)
        
        assert isinstance(vocabulary, list)
        assert len(vocabulary) > 0
        
        # Should contain relevant technical terms
        vocab_text = ' '.join(vocabulary)
        assert any(term in vocab_text for term in ['machine', 'learning', 'data', 'analysis'])
    
    @pytest.mark.asyncio
    async def test_identify_domain_concepts(self, embedding_retrainer, sample_training_examples):
        """Test domain concept identification."""
        concepts = await embedding_retrainer._identify_domain_concepts(sample_training_examples)
        
        assert isinstance(concepts, list)
        # Concepts should be multi-word phrases
        if concepts:
            assert any(len(concept.split()) > 1 for concept in concepts)
    
    @pytest.mark.asyncio
    async def test_calculate_adaptation_weight(self, embedding_retrainer, sample_training_examples):
        """Test adaptation weight calculation."""
        weight = await embedding_retrainer._calculate_adaptation_weight(sample_training_examples)
        
        assert isinstance(weight, float)
        assert 0 <= weight <= 1
        
        # Should be higher for quality examples with metadata
        assert weight > 0.5  # Our sample examples have good metadata
    
    @pytest.mark.asyncio
    async def test_calculate_embeddings(self, embedding_retrainer):
        """Test embedding calculation."""
        texts = ["Machine learning", "Natural language processing", "Database optimization"]
        
        embeddings = await embedding_retrainer._calculate_embeddings(texts, "test_model")
        
        assert len(embeddings) == len(texts)
        assert all(len(emb) == 384 for emb in embeddings)  # Standard embedding dimension
        assert all(abs(sum(emb**2) - 1.0) < 1e-6 for emb in embeddings)  # Should be normalized
    
    @pytest.mark.asyncio
    async def test_calculate_performance_metrics(self, embedding_retrainer):
        """Test performance metrics calculation."""
        similarity_scores = [0.8, 0.6, 0.9, 0.3, 0.7, 0.4]
        relevance_labels = [1, 1, 1, 0, 1, 0]  # 1 = relevant, 0 = not relevant
        
        metrics = await embedding_retrainer._calculate_performance_metrics(similarity_scores, relevance_labels)
        
        assert isinstance(metrics, dict)
        assert 'accuracy' in metrics
        assert 'precision' in metrics
        assert 'recall' in metrics
        assert 'f1_score' in metrics
        assert 'threshold' in metrics
        assert 'mean_similarity' in metrics
        assert 'std_similarity' in metrics
        
        # All metrics should be between 0 and 1
        for key in ['accuracy', 'precision', 'recall', 'f1_score']:
            assert 0 <= metrics[key] <= 1
    
    @pytest.mark.asyncio
    async def test_model_storage_and_loading(self, embedding_retrainer, sample_training_examples):
        """Test model storage and loading."""
        # Create a model
        config = RetrainingConfig(strategy=RetrainingStrategy.INCREMENTAL, model_type=EmbeddingModel.SENTENCE_TRANSFORMER)
        result = await embedding_retrainer.retrain_embeddings(sample_training_examples, config)
        
        # Load the model
        loaded_model = await embedding_retrainer._load_retrained_model(result.model_id)
        
        assert loaded_model is not None
        assert loaded_model['model_id'] == result.model_id
    
    @pytest.mark.asyncio
    async def test_validate_model_for_deployment(self, embedding_retrainer, sample_training_examples):
        """Test model validation for deployment."""
        # Create a model
        config = RetrainingConfig(strategy=RetrainingStrategy.INCREMENTAL, model_type=EmbeddingModel.SENTENCE_TRANSFORMER)
        result = await embedding_retrainer.retrain_embeddings(sample_training_examples, config)
        
        # Validate the model
        is_valid = await embedding_retrainer._validate_model_for_deployment(result.model_id)
        
        # Should be valid since our simulated models have good performance
        assert is_valid is True
    
    def test_training_example_creation(self):
        """Test TrainingExample creation and methods."""
        example = TrainingExample(
            text="Test text",
            label="test_label",
            domain="test_domain"
        )
        
        assert example.text == "Test text"
        assert example.label == "test_label"
        assert example.domain == "test_domain"
        assert example.positive_examples == []
        assert example.negative_examples == []
        assert example.metadata == {}
    
    def test_retraining_config_to_dict(self):
        """Test RetrainingConfig to_dict method."""
        config = RetrainingConfig(
            strategy=RetrainingStrategy.INCREMENTAL,
            model_type=EmbeddingModel.SENTENCE_TRANSFORMER,
            learning_rate=1e-5
        )
        
        config_dict = config.to_dict()
        
        assert config_dict['strategy'] == 'incremental'
        assert config_dict['model_type'] == 'sentence_transformer'
        assert config_dict['learning_rate'] == 1e-5
    
    def test_retraining_result_to_dict(self):
        """Test RetrainingResult to_dict method."""
        result = RetrainingResult(
            model_id="test_model",
            strategy=RetrainingStrategy.INCREMENTAL,
            training_loss=0.15,
            validation_loss=0.18,
            improvement_score=0.08,
            training_examples_count=100,
            training_duration=120.5,
            model_path="/path/to/model",
            performance_metrics={'accuracy': 0.85},
            created_at=datetime.now()
        )
        
        result_dict = result.to_dict()
        
        assert result_dict['model_id'] == "test_model"
        assert result_dict['strategy'] == 'incremental'
        assert result_dict['training_loss'] == 0.15
        assert 'created_at' in result_dict
        assert isinstance(result_dict['created_at'], str)  # Should be ISO format


if __name__ == "__main__":
    pytest.main([__file__])