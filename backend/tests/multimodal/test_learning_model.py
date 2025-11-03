"""
Unit tests for multi-modal learning model.
"""

import pytest
import numpy as np
import asyncio
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from backend.rl.multimodal.learning_model import (
    MultiModalLearningModel,
    MultiModalNeuralNetwork,
    NeuralLayer,
    ActivationFunction,
    RecommendationEngine,
    ModelPersistence,
    ModelConfig,
    ModelType,
    TrainingMode,
    MultiModalTrainingExample,
    TrainingResults,
    Recommendation
)
from backend.rl.multimodal.models import (
    MultiModalFeatures,
    TextFeatures,
    VisualFeatures,
    MultiModalContext,
    DocumentContent,
    ResearchContext,
    VisualElement,
    VisualElementType,
    BoundingBox
)


class TestModelConfig:
    """Test cases for ModelConfig class."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = ModelConfig()
        
        assert config.model_type == ModelType.NEURAL_NETWORK
        assert config.training_mode == TrainingMode.SUPERVISED
        assert config.hidden_layers == [512, 256, 128]
        assert config.activation_function == "relu"
        assert config.dropout_rate == 0.2
        assert config.learning_rate == 0.001
        assert config.batch_size == 32
        assert config.max_epochs == 100
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = ModelConfig(
            model_type=ModelType.TRANSFORMER,
            hidden_layers=[256, 128],
            learning_rate=0.01,
            batch_size=64
        )
        
        assert config.model_type == ModelType.TRANSFORMER
        assert config.hidden_layers == [256, 128]
        assert config.learning_rate == 0.01
        assert config.batch_size == 64


class TestActivationFunction:
    """Test cases for ActivationFunction class."""
    
    def test_relu(self):
        """Test ReLU activation function."""
        x = np.array([-2, -1, 0, 1, 2])
        result = ActivationFunction.relu(x)
        expected = np.array([0, 0, 0, 1, 2])
        
        assert np.array_equal(result, expected)
    
    def test_sigmoid(self):
        """Test sigmoid activation function."""
        x = np.array([0, 1, -1])
        result = ActivationFunction.sigmoid(x)
        
        # Check properties of sigmoid
        assert np.all(result >= 0)
        assert np.all(result <= 1)
        assert abs(result[0] - 0.5) < 1e-6  # sigmoid(0) = 0.5
    
    def test_tanh(self):
        """Test tanh activation function."""
        x = np.array([0, 1, -1])
        result = ActivationFunction.tanh(x)
        
        # Check properties of tanh
        assert np.all(result >= -1)
        assert np.all(result <= 1)
        assert abs(result[0] - 0.0) < 1e-6  # tanh(0) = 0
    
    def test_softmax(self):
        """Test softmax activation function."""
        x = np.array([[1, 2, 3], [1, 1, 1]])
        result = ActivationFunction.softmax(x)
        
        # Check properties of softmax
        assert result.shape == x.shape
        assert np.allclose(np.sum(result, axis=1), 1.0)  # Sum to 1
        assert np.all(result >= 0)  # Non-negative
    
    def test_get_activation(self):
        """Test getting activation function by name."""
        relu_fn = ActivationFunction.get_activation("relu")
        sigmoid_fn = ActivationFunction.get_activation("sigmoid")
        unknown_fn = ActivationFunction.get_activation("unknown")
        
        assert relu_fn == ActivationFunction.relu
        assert sigmoid_fn == ActivationFunction.sigmoid
        assert unknown_fn == ActivationFunction.relu  # Default


class TestNeuralLayer:
    """Test cases for NeuralLayer class."""
    
    def test_layer_initialization(self):
        """Test neural layer initialization."""
        layer = NeuralLayer(input_size=10, output_size=5, activation="relu", dropout_rate=0.2)
        
        assert layer.input_size == 10
        assert layer.output_size == 5
        assert layer.activation_name == "relu"
        assert layer.dropout_rate == 0.2
        assert layer.weights.shape == (10, 5)
        assert layer.biases.shape == (5,)
    
    def test_forward_pass(self):
        """Test forward pass through layer."""
        layer = NeuralLayer(input_size=3, output_size=2, activation="relu")
        x = np.array([[1, 2, 3], [4, 5, 6]])  # Batch of 2 samples
        
        output = layer.forward(x, training=False)
        
        assert output.shape == (2, 2)  # Batch size x output size
        assert np.all(output >= 0)  # ReLU should be non-negative
        assert layer.last_input is not None
        assert layer.last_output is not None
    
    def test_forward_pass_with_dropout(self):
        """Test forward pass with dropout."""
        layer = NeuralLayer(input_size=3, output_size=2, activation="relu", dropout_rate=0.5)
        x = np.array([[1, 2, 3]])
        
        # Training mode (with dropout)
        output_train = layer.forward(x, training=True)
        
        # Inference mode (no dropout)
        output_inference = layer.forward(x, training=False)
        
        assert output_train.shape == output_inference.shape
        # Outputs might be different due to dropout
    
    def test_backward_pass(self):
        """Test backward pass through layer."""
        layer = NeuralLayer(input_size=3, output_size=2, activation="relu")
        x = np.array([[1, 2, 3]])
        
        # Forward pass first
        output = layer.forward(x)
        
        # Backward pass
        grad_output = np.array([[0.1, 0.2]])
        grad_input = layer.backward(grad_output, learning_rate=0.01)
        
        assert grad_input.shape == x.shape
        assert isinstance(grad_input, np.ndarray)


class TestMultiModalNeuralNetwork:
    """Test cases for MultiModalNeuralNetwork class."""
    
    def create_sample_training_data(self, num_samples=10):
        """Create sample training data."""
        training_data = []
        
        for i in range(num_samples):
            # Create sample features
            text_features = TextFeatures(
                embeddings=np.random.rand(50),
                tokens=["word1", "word2"],
                semantic_features={"sentiment": 0.5},
                linguistic_features={"complexity": 0.6},
                domain_features={"technical": 0.7}
            )
            
            visual_features = [VisualFeatures(
                visual_embeddings=np.random.rand(50),
                color_features={"brightness": 0.5},
                texture_features={"roughness": 0.4},
                shape_features={"circularity": 0.6},
                spatial_features={"density": 0.3},
                content_features={"has_text": True}
            )]
            
            multimodal_features = MultiModalFeatures(
                text_features=text_features,
                visual_features=visual_features,
                cross_modal_relationships=[],
                integrated_embedding=np.random.rand(100),
                confidence_scores={"text": 0.8, "visual": 0.7, "integration": 0.75}
            )
            
            # Create training example
            example = MultiModalTrainingExample(
                features=multimodal_features,
                target=np.random.rand()  # Single target value
            )
            
            training_data.append(example)
        
        return training_data
    
    def test_model_initialization(self):
        """Test model initialization."""
        config = ModelConfig()
        model = MultiModalNeuralNetwork(config)
        
        assert model.config == config
        assert model.layers == []
        assert not model.is_trained
        assert "loss" in model.training_history
        assert "accuracy" in model.training_history
    
    def test_build_model(self):
        """Test model building."""
        config = ModelConfig(hidden_layers=[64, 32])
        model = MultiModalNeuralNetwork(config)
        
        model.build_model(input_size=100, output_size=1)
        
        # Should have hidden layers + output layer
        assert len(model.layers) == 3  # 2 hidden + 1 output
        assert model.layers[0].input_size == 100
        assert model.layers[0].output_size == 64
        assert model.layers[1].input_size == 64
        assert model.layers[1].output_size == 32
        assert model.layers[2].input_size == 32
        assert model.layers[2].output_size == 1
    
    @pytest.mark.asyncio
    async def test_prepare_training_data(self):
        """Test training data preparation."""
        config = ModelConfig()
        model = MultiModalNeuralNetwork(config)
        training_data = self.create_sample_training_data(5)
        
        X, y = await model._prepare_training_data(training_data)
        
        assert X.shape[0] == 5  # Number of samples
        assert y.shape[0] == 5  # Number of targets
        assert X.shape[1] > 0  # Feature dimension
        assert isinstance(X, np.ndarray)
        assert isinstance(y, np.ndarray)
    
    @pytest.mark.asyncio
    async def test_features_to_vector(self):
        """Test feature to vector conversion."""
        config = ModelConfig()
        model = MultiModalNeuralNetwork(config)
        
        # Create sample features
        text_features = TextFeatures(
            embeddings=np.random.rand(50),
            tokens=["test"],
            semantic_features={},
            linguistic_features={},
            domain_features={}
        )
        
        visual_features = [VisualFeatures(
            visual_embeddings=np.random.rand(50),
            color_features={}, texture_features={}, shape_features={},
            spatial_features={}, content_features={}
        )]
        
        multimodal_features = MultiModalFeatures(
            text_features=text_features,
            visual_features=visual_features,
            cross_modal_relationships=[],
            integrated_embedding=np.random.rand(100),
            confidence_scores={"text": 0.8, "visual": 0.7}
        )
        
        vector = await model._features_to_vector(multimodal_features)
        
        assert isinstance(vector, np.ndarray)
        assert len(vector) > 100  # Should include embedding + confidence scores
    
    @pytest.mark.asyncio
    async def test_target_to_vector(self):
        """Test target to vector conversion."""
        config = ModelConfig()
        model = MultiModalNeuralNetwork(config)
        
        # Test different target types
        float_target = 0.5
        int_target = 1
        array_target = np.array([0.1, 0.2, 0.3])
        dict_target = {"score1": 0.8, "score2": 0.6}
        
        float_vector = await model._target_to_vector(float_target)
        int_vector = await model._target_to_vector(int_target)
        array_vector = await model._target_to_vector(array_target)
        dict_vector = await model._target_to_vector(dict_target)
        
        assert isinstance(float_vector, np.ndarray)
        assert len(float_vector) == 1
        assert float_vector[0] == 0.5
        
        assert isinstance(int_vector, np.ndarray)
        assert len(int_vector) == 1
        assert int_vector[0] == 1
        
        assert isinstance(array_vector, np.ndarray)
        assert len(array_vector) == 3
        
        assert isinstance(dict_vector, np.ndarray)
        assert len(dict_vector) == 2
    
    @pytest.mark.asyncio
    async def test_forward_pass(self):
        """Test forward pass through network."""
        config = ModelConfig(hidden_layers=[32, 16])
        model = MultiModalNeuralNetwork(config)
        model.build_model(input_size=50, output_size=1)
        
        x = np.random.rand(3, 50)  # Batch of 3 samples
        
        output = await model._forward_pass(x, training=False)
        
        assert output.shape == (3, 1)
        assert isinstance(output, np.ndarray)
    
    @pytest.mark.asyncio
    async def test_calculate_loss(self):
        """Test loss calculation."""
        config = ModelConfig()
        model = MultiModalNeuralNetwork(config)
        
        predictions = np.array([[0.8], [0.6], [0.4]])
        targets = np.array([[1.0], [0.5], [0.3]])
        
        loss = await model._calculate_loss(predictions, targets)
        
        assert isinstance(loss, float)
        assert loss >= 0  # MSE should be non-negative
    
    @pytest.mark.asyncio
    async def test_calculate_accuracy(self):
        """Test accuracy calculation."""
        config = ModelConfig()
        model = MultiModalNeuralNetwork(config)
        
        # Perfect predictions
        predictions = np.array([[1.0], [0.5], [0.3]])
        targets = np.array([[1.0], [0.5], [0.3]])
        
        accuracy = await model._calculate_accuracy(predictions, targets)
        
        assert isinstance(accuracy, float)
        assert 0 <= accuracy <= 1
        assert accuracy == 1.0  # Perfect predictions should give accuracy 1
    
    @pytest.mark.asyncio
    async def test_train_model(self):
        """Test model training."""
        config = ModelConfig(max_epochs=5, early_stopping_patience=3)
        model = MultiModalNeuralNetwork(config)
        training_data = self.create_sample_training_data(10)
        
        results = await model.train(training_data)
        
        assert isinstance(results, TrainingResults)
        assert model.is_trained
        assert len(model.training_history["loss"]) > 0
        assert len(model.training_history["accuracy"]) > 0
        assert results.total_epochs <= config.max_epochs
        assert results.training_time > 0
        assert isinstance(results.final_metrics, dict)
    
    @pytest.mark.asyncio
    async def test_predict(self):
        """Test model prediction."""
        config = ModelConfig(max_epochs=2)
        model = MultiModalNeuralNetwork(config)
        training_data = self.create_sample_training_data(5)
        
        # Train model first
        await model.train(training_data)
        
        # Make prediction
        test_features = training_data[0].features
        prediction = await model.predict(test_features)
        
        assert isinstance(prediction, np.ndarray)
        assert len(prediction) > 0
    
    @pytest.mark.asyncio
    async def test_predict_untrained_model(self):
        """Test prediction with untrained model."""
        config = ModelConfig()
        model = MultiModalNeuralNetwork(config)
        training_data = self.create_sample_training_data(1)
        
        with pytest.raises(ValueError, match="Model must be trained"):
            await model.predict(training_data[0].features)


class TestRecommendationEngine:
    """Test cases for RecommendationEngine class."""
    
    def create_sample_context(self):
        """Create sample multi-modal context."""
        doc_content = DocumentContent(
            document_id="doc1",
            text_content="Sample document content",
            raw_text="Sample document content",
            structured_content={}
        )
        
        research_context = ResearchContext(
            research_domain="machine_learning",
            research_goals=["understand", "implement"]
        )
        
        visual_elements = [
            VisualElement(
                element_id="elem1",
                element_type=VisualElementType.CHART,
                bounding_box=BoundingBox(x=10, y=20, width=100, height=80),
                confidence=0.9
            )
        ]
        
        return MultiModalContext(
            context_id="ctx1",
            document_content=doc_content,
            visual_elements=visual_elements,
            user_interaction_history=[],
            research_context=research_context
        )
    
    @pytest.mark.asyncio
    async def test_generate_recommendations(self):
        """Test recommendation generation."""
        # Create mock model
        mock_model = Mock()
        engine = RecommendationEngine(mock_model)
        context = self.create_sample_context()
        
        recommendations = await engine.generate_recommendations(context, num_recommendations=3)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) == 3
        
        for rec in recommendations:
            assert isinstance(rec, Recommendation)
            assert rec.recommendation_id
            assert rec.content
            assert 0 <= rec.confidence <= 1
            assert rec.reasoning
            assert isinstance(rec.metadata, dict)
        
        # Should be sorted by confidence (descending)
        confidences = [rec.confidence for rec in recommendations]
        assert confidences == sorted(confidences, reverse=True)
    
    def test_recommendation_validation(self):
        """Test recommendation validation."""
        # Valid recommendation
        valid_rec = Recommendation(
            recommendation_id="rec1",
            content="Test recommendation",
            confidence=0.8,
            reasoning="Test reasoning"
        )
        
        assert valid_rec.confidence == 0.8
        
        # Invalid confidence (too high)
        with pytest.raises(ValueError, match="Confidence must be between 0 and 1"):
            Recommendation(
                recommendation_id="rec2",
                content="Test",
                confidence=1.5,
                reasoning="Test"
            )
        
        # Invalid confidence (negative)
        with pytest.raises(ValueError, match="Confidence must be between 0 and 1"):
            Recommendation(
                recommendation_id="rec3",
                content="Test",
                confidence=-0.1,
                reasoning="Test"
            )


class TestModelPersistence:
    """Test cases for ModelPersistence class."""
    
    def create_sample_model(self):
        """Create a sample trained model."""
        config = ModelConfig(hidden_layers=[32, 16])
        model = MultiModalNeuralNetwork(config)
        model.build_model(input_size=50, output_size=1)
        model.is_trained = True
        model.training_history = {"loss": [0.5, 0.3, 0.1], "accuracy": [0.6, 0.8, 0.9]}
        return model
    
    @pytest.mark.asyncio
    async def test_save_and_load_model(self):
        """Test saving and loading model."""
        model = self.create_sample_model()
        
        with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as tmp_file:
            filepath = tmp_file.name
        
        try:
            # Save model
            success = await ModelPersistence.save_model(model, filepath)
            assert success
            assert os.path.exists(filepath)
            
            # Load model
            loaded_model = await ModelPersistence.load_model(filepath)
            assert loaded_model is not None
            assert loaded_model.is_trained == model.is_trained
            assert len(loaded_model.layers) == len(model.layers)
            assert loaded_model.training_history == model.training_history
            
            # Check layer parameters
            for orig_layer, loaded_layer in zip(model.layers, loaded_model.layers):
                assert orig_layer.input_size == loaded_layer.input_size
                assert orig_layer.output_size == loaded_layer.output_size
                assert np.array_equal(orig_layer.weights, loaded_layer.weights)
                assert np.array_equal(orig_layer.biases, loaded_layer.biases)
        
        finally:
            # Clean up
            if os.path.exists(filepath):
                os.unlink(filepath)
    
    @pytest.mark.asyncio
    async def test_load_nonexistent_model(self):
        """Test loading non-existent model."""
        loaded_model = await ModelPersistence.load_model("nonexistent_file.pkl")
        assert loaded_model is None
    
    @pytest.mark.asyncio
    async def test_save_model_invalid_path(self):
        """Test saving model to invalid path."""
        model = self.create_sample_model()
        
        # Try to save to invalid path (directory that doesn't exist and can't be created)
        invalid_path = "/invalid/path/that/does/not/exist/model.pkl"
        
        # Should handle error gracefully
        success = await ModelPersistence.save_model(model, invalid_path)
        # Depending on permissions, this might succeed (if directory can be created) or fail
        assert isinstance(success, bool)


class TestMultiModalLearningModel:
    """Test cases for MultiModalLearningModel class."""
    
    def create_sample_training_data(self, num_samples=5):
        """Create sample training data."""
        training_data = []
        
        for i in range(num_samples):
            text_features = TextFeatures(
                embeddings=np.random.rand(50),
                tokens=["word1", "word2"],
                semantic_features={"sentiment": 0.5},
                linguistic_features={"complexity": 0.6},
                domain_features={"technical": 0.7}
            )
            
            visual_features = [VisualFeatures(
                visual_embeddings=np.random.rand(50),
                color_features={"brightness": 0.5},
                texture_features={"roughness": 0.4},
                shape_features={"circularity": 0.6},
                spatial_features={"density": 0.3},
                content_features={"has_text": True}
            )]
            
            multimodal_features = MultiModalFeatures(
                text_features=text_features,
                visual_features=visual_features,
                cross_modal_relationships=[],
                integrated_embedding=np.random.rand(100),
                confidence_scores={"text": 0.8, "visual": 0.7, "integration": 0.75}
            )
            
            example = MultiModalTrainingExample(
                features=multimodal_features,
                target=np.random.rand()
            )
            
            training_data.append(example)
        
        return training_data
    
    def create_sample_context(self):
        """Create sample multi-modal context."""
        doc_content = DocumentContent(
            document_id="doc1",
            text_content="Sample document",
            raw_text="Sample document",
            structured_content={}
        )
        
        research_context = ResearchContext(
            research_domain="ai",
            research_goals=["learn"]
        )
        
        return MultiModalContext(
            context_id="ctx1",
            document_content=doc_content,
            visual_elements=[],
            user_interaction_history=[],
            research_context=research_context
        )
    
    def test_model_initialization(self):
        """Test model initialization."""
        model = MultiModalLearningModel()
        
        assert isinstance(model.config, ModelConfig)
        assert isinstance(model.model, MultiModalNeuralNetwork)
        assert isinstance(model.recommendation_engine, RecommendationEngine)
        assert not model.is_trained
    
    def test_model_initialization_with_config(self):
        """Test model initialization with custom config."""
        config = ModelConfig(learning_rate=0.01, batch_size=64)
        model = MultiModalLearningModel(config)
        
        assert model.config == config
        assert model.config.learning_rate == 0.01
        assert model.config.batch_size == 64
    
    @pytest.mark.asyncio
    async def test_train_on_multimodal_data(self):
        """Test training on multi-modal data."""
        config = ModelConfig(max_epochs=3, save_best_only=False)
        model = MultiModalLearningModel(config)
        training_data = self.create_sample_training_data(5)
        
        results = await model.train_on_multimodal_data(training_data)
        
        assert isinstance(results, TrainingResults)
        assert model.is_trained
        assert results.total_epochs <= config.max_epochs
        assert results.training_time > 0
        assert isinstance(results.final_metrics, dict)
    
    @pytest.mark.asyncio
    async def test_train_empty_data(self):
        """Test training with empty data."""
        model = MultiModalLearningModel()
        
        with pytest.raises(ValueError, match="Training data cannot be empty"):
            await model.train_on_multimodal_data([])
    
    @pytest.mark.asyncio
    async def test_generate_multimodal_recommendations(self):
        """Test generating multi-modal recommendations."""
        model = MultiModalLearningModel()
        context = self.create_sample_context()
        
        recommendations = await model.generate_multimodal_recommendations(context)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        
        for rec in recommendations:
            assert isinstance(rec, Recommendation)
    
    @pytest.mark.asyncio
    async def test_predict_from_features(self):
        """Test prediction from features."""
        config = ModelConfig(max_epochs=2)
        model = MultiModalLearningModel(config)
        training_data = self.create_sample_training_data(3)
        
        # Train model first
        await model.train_on_multimodal_data(training_data)
        
        # Make prediction
        test_features = training_data[0].features
        prediction_result = await model.predict_from_features(test_features)
        
        assert isinstance(prediction_result, dict)
        assert "prediction" in prediction_result
        assert "confidence" in prediction_result
        assert "feature_quality" in prediction_result
        assert "metadata" in prediction_result
        
        assert isinstance(prediction_result["prediction"], list)
        assert 0 <= prediction_result["confidence"] <= 1
    
    @pytest.mark.asyncio
    async def test_predict_untrained_model(self):
        """Test prediction with untrained model."""
        model = MultiModalLearningModel()
        training_data = self.create_sample_training_data(1)
        
        with pytest.raises(ValueError, match="Model must be trained"):
            await model.predict_from_features(training_data[0].features)
    
    @pytest.mark.asyncio
    async def test_evaluate_model(self):
        """Test model evaluation."""
        config = ModelConfig(max_epochs=2)
        model = MultiModalLearningModel(config)
        training_data = self.create_sample_training_data(5)
        test_data = self.create_sample_training_data(3)
        
        # Train model first
        await model.train_on_multimodal_data(training_data)
        
        # Evaluate model
        metrics = await model.evaluate_model(test_data)
        
        assert isinstance(metrics, dict)
        assert "mse" in metrics
        assert "mae" in metrics
        assert "rmse" in metrics
        assert "r_squared" in metrics
        assert "correlation" in metrics
        
        for metric_value in metrics.values():
            assert isinstance(metric_value, float)
    
    @pytest.mark.asyncio
    async def test_evaluate_untrained_model(self):
        """Test evaluation with untrained model."""
        model = MultiModalLearningModel()
        test_data = self.create_sample_training_data(3)
        
        with pytest.raises(ValueError, match="Model must be trained"):
            await model.evaluate_model(test_data)
    
    @pytest.mark.asyncio
    async def test_evaluate_empty_test_data(self):
        """Test evaluation with empty test data."""
        config = ModelConfig(max_epochs=1)
        model = MultiModalLearningModel(config)
        training_data = self.create_sample_training_data(3)
        
        # Train model first
        await model.train_on_multimodal_data(training_data)
        
        with pytest.raises(ValueError, match="Test data cannot be empty"):
            await model.evaluate_model([])
    
    @pytest.mark.asyncio
    async def test_save_and_load_model(self):
        """Test saving and loading model."""
        config = ModelConfig(max_epochs=2)
        model = MultiModalLearningModel(config)
        training_data = self.create_sample_training_data(3)
        
        # Train model
        await model.train_on_multimodal_data(training_data)
        
        with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as tmp_file:
            filepath = tmp_file.name
        
        try:
            # Save model
            success = await model.save_model(filepath)
            assert success
            
            # Create new model and load
            new_model = MultiModalLearningModel(config)
            load_success = await new_model.load_model(filepath)
            
            assert load_success
            assert new_model.is_trained
        
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)
    
    def test_get_model_info(self):
        """Test getting model information."""
        config = ModelConfig(hidden_layers=[64, 32], learning_rate=0.01)
        model = MultiModalLearningModel(config)
        
        info = model.get_model_info()
        
        assert isinstance(info, dict)
        assert info["model_type"] == config.model_type.value
        assert info["training_mode"] == config.training_mode.value
        assert info["is_trained"] == False
        assert info["architecture"]["hidden_layers"] == [64, 32]
        assert info["training_config"]["learning_rate"] == 0.01
    
    @pytest.mark.asyncio
    async def test_get_model_info_trained(self):
        """Test getting model information for trained model."""
        config = ModelConfig(max_epochs=2)
        model = MultiModalLearningModel(config)
        training_data = self.create_sample_training_data(3)
        
        # Train model
        await model.train_on_multimodal_data(training_data)
        
        info = model.get_model_info()
        
        assert info["is_trained"] == True
        assert "training_history" in info
        assert "epochs_trained" in info["training_history"]
        assert "final_loss" in info["training_history"]
        assert "final_accuracy" in info["training_history"]


class TestMultiModalTrainingExample:
    """Test cases for MultiModalTrainingExample class."""
    
    def create_sample_features(self):
        """Create sample multi-modal features."""
        text_features = TextFeatures(
            embeddings=np.random.rand(50),
            tokens=["test"],
            semantic_features={},
            linguistic_features={},
            domain_features={}
        )
        
        visual_features = [VisualFeatures(
            visual_embeddings=np.random.rand(50),
            color_features={}, texture_features={}, shape_features={},
            spatial_features={}, content_features={}
        )]
        
        return MultiModalFeatures(
            text_features=text_features,
            visual_features=visual_features,
            cross_modal_relationships=[],
            integrated_embedding=np.random.rand(100),
            confidence_scores={"text": 0.8, "visual": 0.7}
        )
    
    def test_valid_training_example(self):
        """Test creating valid training example."""
        features = self.create_sample_features()
        target = 0.5
        
        example = MultiModalTrainingExample(
            features=features,
            target=target
        )
        
        assert example.features == features
        assert example.target == target
        assert example.context is None
        assert isinstance(example.metadata, dict)
    
    def test_training_example_with_context(self):
        """Test training example with context."""
        features = self.create_sample_features()
        target = [0.1, 0.2, 0.3]
        
        doc_content = DocumentContent(
            document_id="doc1",
            text_content="test",
            raw_text="test",
            structured_content={}
        )
        
        research_context = ResearchContext(
            research_domain="test",
            research_goals=["test"]
        )
        
        context = MultiModalContext(
            context_id="ctx1",
            document_content=doc_content,
            visual_elements=[],
            user_interaction_history=[],
            research_context=research_context
        )
        
        example = MultiModalTrainingExample(
            features=features,
            target=target,
            context=context,
            metadata={"source": "test"}
        )
        
        assert example.context == context
        assert example.metadata["source"] == "test"
    
    def test_invalid_training_example(self):
        """Test validation of training example."""
        # None features
        with pytest.raises(ValueError, match="Features cannot be None"):
            MultiModalTrainingExample(
                features=None,
                target=0.5
            )
        
        # None target
        features = self.create_sample_features()
        with pytest.raises(ValueError, match="Target cannot be None"):
            MultiModalTrainingExample(
                features=features,
                target=None
            )


class TestIntegration:
    """Integration tests for multi-modal learning model."""
    
    def create_comprehensive_training_data(self, num_samples=20):
        """Create comprehensive training data for integration testing."""
        training_data = []
        
        for i in range(num_samples):
            # Create varied features
            text_features = TextFeatures(
                embeddings=np.random.rand(128),
                tokens=[f"word_{j}" for j in range(np.random.randint(5, 15))],
                semantic_features={
                    "sentiment": np.random.rand(),
                    "complexity": np.random.rand(),
                    "formality": np.random.rand()
                },
                linguistic_features={
                    "pos_diversity": np.random.rand(),
                    "syntax_complexity": np.random.rand()
                },
                domain_features={
                    "technical": np.random.rand(),
                    "academic": np.random.rand()
                }
            )
            
            visual_features = [VisualFeatures(
                visual_embeddings=np.random.rand(128),
                color_features={
                    "brightness": np.random.rand(),
                    "contrast": np.random.rand()
                },
                texture_features={
                    "roughness": np.random.rand(),
                    "uniformity": np.random.rand()
                },
                shape_features={
                    "circularity": np.random.rand(),
                    "rectangularity": np.random.rand()
                },
                spatial_features={
                    "density": np.random.rand(),
                    "symmetry": np.random.rand()
                },
                content_features={
                    "has_text": np.random.rand() > 0.5,
                    "complexity": np.random.rand()
                }
            )]
            
            multimodal_features = MultiModalFeatures(
                text_features=text_features,
                visual_features=visual_features,
                cross_modal_relationships=[],
                integrated_embedding=np.random.rand(200),
                confidence_scores={
                    "text": np.random.uniform(0.5, 1.0),
                    "visual": np.random.uniform(0.5, 1.0),
                    "integration": np.random.uniform(0.5, 1.0)
                }
            )
            
            # Create target based on some features (to make learning possible)
            target = (
                np.mean(text_features.embeddings[:10]) * 0.5 +
                np.mean(visual_features[0].visual_embeddings[:10]) * 0.5
            )
            
            example = MultiModalTrainingExample(
                features=multimodal_features,
                target=target,
                metadata={"sample_id": i}
            )
            
            training_data.append(example)
        
        return training_data
    
    @pytest.mark.asyncio
    async def test_end_to_end_training_and_prediction(self):
        """Test complete end-to-end training and prediction workflow."""
        config = ModelConfig(
            hidden_layers=[128, 64, 32],
            max_epochs=10,
            learning_rate=0.01,
            early_stopping_patience=5
        )
        
        model = MultiModalLearningModel(config)
        
        # Create training and test data
        all_data = self.create_comprehensive_training_data(30)
        training_data = all_data[:20]
        test_data = all_data[20:]
        
        # Train model
        training_results = await model.train_on_multimodal_data(training_data)
        
        assert isinstance(training_results, TrainingResults)
        assert model.is_trained
        assert training_results.training_time > 0
        
        # Evaluate model
        evaluation_metrics = await model.evaluate_model(test_data)
        
        assert isinstance(evaluation_metrics, dict)
        assert "mse" in evaluation_metrics
        assert "r_squared" in evaluation_metrics
        
        # Make individual predictions
        for test_example in test_data[:3]:
            prediction_result = await model.predict_from_features(test_example.features)
            
            assert isinstance(prediction_result, dict)
            assert "prediction" in prediction_result
            assert "confidence" in prediction_result
        
        # Generate recommendations
        context = MultiModalContext(
            context_id="test_ctx",
            document_content=DocumentContent(
                document_id="test_doc",
                text_content="Test document for recommendations",
                raw_text="Test document for recommendations",
                structured_content={}
            ),
            visual_elements=[],
            user_interaction_history=[],
            research_context=ResearchContext(
                research_domain="test_domain",
                research_goals=["test_goal"]
            )
        )
        
        recommendations = await model.generate_multimodal_recommendations(context)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        
        for rec in recommendations:
            assert isinstance(rec, Recommendation)
            assert 0 <= rec.confidence <= 1
    
    @pytest.mark.asyncio
    async def test_model_persistence_integration(self):
        """Test model persistence in integration scenario."""
        config = ModelConfig(max_epochs=5)
        model = MultiModalLearningModel(config)
        training_data = self.create_comprehensive_training_data(10)
        
        # Train model
        await model.train_on_multimodal_data(training_data)
        
        with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as tmp_file:
            filepath = tmp_file.name
        
        try:
            # Save model
            save_success = await model.save_model(filepath)
            assert save_success
            
            # Create new model and load
            new_model = MultiModalLearningModel(config)
            load_success = await new_model.load_model(filepath)
            assert load_success
            
            # Test that loaded model works
            test_features = training_data[0].features
            
            original_prediction = await model.predict_from_features(test_features)
            loaded_prediction = await new_model.predict_from_features(test_features)
            
            # Predictions should be identical
            assert np.allclose(
                original_prediction["prediction"],
                loaded_prediction["prediction"]
            )
        
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)
    
    @pytest.mark.asyncio
    async def test_different_model_configurations(self):
        """Test training with different model configurations."""
        configurations = [
            ModelConfig(hidden_layers=[64], max_epochs=3),
            ModelConfig(hidden_layers=[128, 64], max_epochs=3),
            ModelConfig(hidden_layers=[256, 128, 64], max_epochs=3),
        ]
        
        training_data = self.create_comprehensive_training_data(15)
        
        for config in configurations:
            model = MultiModalLearningModel(config)
            
            # Train model
            results = await model.train_on_multimodal_data(training_data)
            
            assert isinstance(results, TrainingResults)
            assert model.is_trained
            
            # Test prediction
            test_features = training_data[0].features
            prediction = await model.predict_from_features(test_features)
            
            assert isinstance(prediction, dict)
            assert "prediction" in prediction
    
    @pytest.mark.asyncio
    async def test_performance_with_large_dataset(self):
        """Test performance with larger dataset."""
        config = ModelConfig(
            hidden_layers=[128, 64],
            max_epochs=5,
            batch_size=16
        )
        
        model = MultiModalLearningModel(config)
        
        # Create larger dataset
        large_training_data = self.create_comprehensive_training_data(100)
        
        # Should complete training without timeout or memory issues
        results = await model.train_on_multimodal_data(large_training_data)
        
        assert isinstance(results, TrainingResults)
        assert model.is_trained
        assert results.training_time > 0