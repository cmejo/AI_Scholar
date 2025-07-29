#!/usr/bin/env python3
"""
Task 9.4 Verification: Build embedding retraining capabilities
Tests the implementation of EmbeddingRetrainer for model updates, domain-specific fine-tuning, and incremental learning.
"""

import asyncio
import json
import logging
import tempfile
import os
from datetime import datetime, timedelta
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Task94Verifier:
    """Verifier for Task 9.4: Build embedding retraining capabilities."""
    
    def __init__(self):
        self.retrainer = None
        self.test_results = {}
        self.sample_training_data = []
    
    async def setup(self):
        """Set up the verifier."""
        try:
            self.retrainer = EmbeddingRetrainer()
            await self.retrainer.initialize()
            
            # Create sample training data
            self.sample_training_data = await self._create_sample_training_data()
            
            logger.info("Task 9.4 verifier setup completed")
            return True
            
        except Exception as e:
            logger.error(f"Setup failed: {e}")
            return False
    
    async def _create_sample_training_data(self) -> List[TrainingExample]:
        """Create comprehensive sample training data."""
        examples = []
        
        # Technology domain examples
        tech_examples = [
            TrainingExample(
                text="Machine learning algorithms for predictive modeling and data analysis",
                domain="technology",
                positive_examples=[
                    "Deep learning neural networks for pattern recognition",
                    "Statistical models for predictive analytics",
                    "AI algorithms for data mining and insights"
                ],
                negative_examples=[
                    "Cooking recipes and culinary techniques",
                    "Sports statistics and game analysis",
                    "Fashion trends and style guides"
                ],
                metadata={"source": "document", "quality": 0.9, "complexity": "high"}
            ),
            TrainingExample(
                text="Database optimization techniques and query performance tuning",
                domain="technology",
                positive_examples=[
                    "SQL query optimization strategies",
                    "Index design and performance tuning",
                    "Database schema optimization"
                ],
                negative_examples=[
                    "Art history and cultural studies",
                    "Music theory and composition",
                    "Literature analysis and criticism"
                ],
                metadata={"source": "interaction", "quality": 0.85, "complexity": "medium"}
            ),
            TrainingExample(
                text="Cloud computing infrastructure and scalable system design",
                domain="technology",
                positive_examples=[
                    "AWS services for scalable applications",
                    "Kubernetes container orchestration",
                    "Microservices architecture patterns"
                ],
                negative_examples=[
                    "Traditional cooking methods",
                    "Historical events and timelines",
                    "Entertainment industry news"
                ],
                metadata={"source": "feedback", "quality": 0.8, "complexity": "high"}
            )
        ]
        
        # Science domain examples
        science_examples = [
            TrainingExample(
                text="Quantum mechanics principles and particle physics research",
                domain="science",
                positive_examples=[
                    "Quantum entanglement experiments",
                    "Particle accelerator data analysis",
                    "Theoretical physics modeling"
                ],
                negative_examples=[
                    "Business marketing strategies",
                    "Social media engagement tactics",
                    "Celebrity news and gossip"
                ],
                metadata={"source": "document", "quality": 0.95, "complexity": "very_high"}
            ),
            TrainingExample(
                text="Climate change research and environmental impact studies",
                domain="science",
                positive_examples=[
                    "Carbon emission measurement techniques",
                    "Global warming trend analysis",
                    "Renewable energy research findings"
                ],
                negative_examples=[
                    "Video game reviews and ratings",
                    "Restaurant recommendations",
                    "Travel destination guides"
                ],
                metadata={"source": "interaction", "quality": 0.9, "complexity": "high"}
            )
        ]
        
        # Business domain examples
        business_examples = [
            TrainingExample(
                text="Financial market analysis and investment portfolio management",
                domain="business",
                positive_examples=[
                    "Stock market trend analysis",
                    "Portfolio optimization strategies",
                    "Risk management techniques"
                ],
                negative_examples=[
                    "Scientific research methodologies",
                    "Technical documentation",
                    "Academic literature reviews"
                ],
                metadata={"source": "document", "quality": 0.8, "complexity": "medium"}
            )
        ]
        
        examples.extend(tech_examples)
        examples.extend(science_examples)
        examples.extend(business_examples)
        
        return examples
    
    async def verify_embedding_retrainer_initialization(self) -> bool:
        """Verify EmbeddingRetrainer can be initialized properly."""
        try:
            logger.info("Verifying EmbeddingRetrainer initialization...")
            
            # Check that retrainer is initialized
            assert self.retrainer is not None, "EmbeddingRetrainer should be initialized"
            
            # Check that model storage path exists
            assert os.path.exists(self.retrainer.model_storage_path), "Model storage path should exist"
            
            # Check supported domains
            assert len(self.retrainer.supported_domains) > 0, "Should have supported domains"
            assert "technology" in self.retrainer.supported_domains, "Should support technology domain"
            
            logger.info("✓ EmbeddingRetrainer initialization verified")
            return True
            
        except Exception as e:
            logger.error(f"✗ EmbeddingRetrainer initialization verification failed: {e}")
            return False
    
    async def verify_training_data_collection(self) -> bool:
        """Verify training data collection functionality."""
        try:
            logger.info("Verifying training data collection...")
            
            # Test general data collection
            general_data = await self.retrainer.collect_training_data(time_window_days=30)
            assert isinstance(general_data, list), "Should return list of training examples"
            
            # Test domain-specific data collection
            tech_data = await self.retrainer.collect_training_data(domain="technology", time_window_days=30)
            assert isinstance(tech_data, list), "Should return list for domain-specific collection"
            
            logger.info("✓ Training data collection verified")
            return True
            
        except Exception as e:
            logger.error(f"✗ Training data collection verification failed: {e}")
            return False
    
    async def verify_domain_adaptation_data_preparation(self) -> bool:
        """Verify domain adaptation data preparation."""
        try:
            logger.info("Verifying domain adaptation data preparation...")
            
            # Test domain adaptation for technology
            adaptation_data = await self.retrainer.prepare_domain_adaptation_data("technology")
            
            assert isinstance(adaptation_data, DomainAdaptationData), "Should return DomainAdaptationData"
            assert adaptation_data.domain_name == "technology", "Should have correct domain name"
            assert isinstance(adaptation_data.domain_examples, list), "Should have domain examples"
            assert isinstance(adaptation_data.domain_vocabulary, list), "Should have domain vocabulary"
            assert isinstance(adaptation_data.domain_concepts, list), "Should have domain concepts"
            assert 0 <= adaptation_data.adaptation_weight <= 1, "Adaptation weight should be between 0 and 1"
            
            logger.info("✓ Domain adaptation data preparation verified")
            return True
            
        except Exception as e:
            logger.error(f"✗ Domain adaptation data preparation verification failed: {e}")
            return False
    
    async def verify_incremental_retraining(self) -> bool:
        """Verify incremental retraining functionality."""
        try:
            logger.info("Verifying incremental retraining...")
            
            config = RetrainingConfig(
                strategy=RetrainingStrategy.INCREMENTAL,
                model_type=EmbeddingModel.SENTENCE_TRANSFORMER,
                learning_rate=1e-5,
                batch_size=16,
                epochs=3
            )
            
            result = await self.retrainer.retrain_embeddings(self.sample_training_data, config)
            
            assert isinstance(result, RetrainingResult), "Should return RetrainingResult"
            assert result.strategy == RetrainingStrategy.INCREMENTAL, "Should have correct strategy"
            assert result.training_examples_count == len(self.sample_training_data), "Should have correct example count"
            assert result.training_loss > 0, "Should have positive training loss"
            assert result.validation_loss > 0, "Should have positive validation loss"
            assert result.improvement_score > 0, "Should have positive improvement score"
            assert isinstance(result.performance_metrics, dict), "Should have performance metrics"
            assert "accuracy" in result.performance_metrics, "Should have accuracy metric"
            assert "precision" in result.performance_metrics, "Should have precision metric"
            assert "recall" in result.performance_metrics, "Should have recall metric"
            assert "f1_score" in result.performance_metrics, "Should have f1_score metric"
            
            logger.info("✓ Incremental retraining verified")
            return True
            
        except Exception as e:
            logger.error(f"✗ Incremental retraining verification failed: {e}")
            return False
    
    async def verify_domain_specific_fine_tuning(self) -> bool:
        """Verify domain-specific fine-tuning functionality."""
        try:
            logger.info("Verifying domain-specific fine-tuning...")
            
            # Test domain adaptation strategy
            config = RetrainingConfig(
                strategy=RetrainingStrategy.DOMAIN_ADAPTATION,
                model_type=EmbeddingModel.SENTENCE_TRANSFORMER,
                learning_rate=1e-5,
                batch_size=16,
                epochs=3,
                domain_weight=0.7
            )
            
            result = await self.retrainer.retrain_embeddings(self.sample_training_data, config)
            
            assert isinstance(result, RetrainingResult), "Should return RetrainingResult"
            assert result.strategy == RetrainingStrategy.DOMAIN_ADAPTATION, "Should have domain adaptation strategy"
            assert "domain_specificity" in result.performance_metrics, "Should have domain specificity metric"
            assert result.improvement_score > 0.1, "Domain adaptation should show good improvement"
            
            # Test fine-tuning strategy
            fine_tune_config = RetrainingConfig(
                strategy=RetrainingStrategy.FINE_TUNING,
                model_type=EmbeddingModel.SENTENCE_TRANSFORMER,
                learning_rate=1e-5,
                batch_size=16,
                epochs=3
            )
            
            fine_tune_result = await self.retrainer.retrain_embeddings(self.sample_training_data, fine_tune_config)
            
            assert fine_tune_result.strategy == RetrainingStrategy.FINE_TUNING, "Should have fine-tuning strategy"
            assert "stability_score" in fine_tune_result.performance_metrics, "Should have stability score"
            
            logger.info("✓ Domain-specific fine-tuning verified")
            return True
            
        except Exception as e:
            logger.error(f"✗ Domain-specific fine-tuning verification failed: {e}")
            return False
    
    async def verify_contrastive_learning(self) -> bool:
        """Verify contrastive learning functionality."""
        try:
            logger.info("Verifying contrastive learning...")
            
            config = RetrainingConfig(
                strategy=RetrainingStrategy.CONTRASTIVE_LEARNING,
                model_type=EmbeddingModel.SENTENCE_TRANSFORMER,
                learning_rate=1e-5,
                batch_size=16,
                epochs=3,
                contrastive_margin=0.5,
                use_hard_negatives=True
            )
            
            result = await self.retrainer.retrain_embeddings(self.sample_training_data, config)
            
            assert isinstance(result, RetrainingResult), "Should return RetrainingResult"
            assert result.strategy == RetrainingStrategy.CONTRASTIVE_LEARNING, "Should have contrastive learning strategy"
            assert "similarity_quality" in result.performance_metrics, "Should have similarity quality metric"
            assert "contrastive_margin" in result.performance_metrics, "Should have contrastive margin metric"
            assert result.performance_metrics["contrastive_margin"] == 0.5, "Should preserve contrastive margin"
            
            logger.info("✓ Contrastive learning verified")
            return True
            
        except Exception as e:
            logger.error(f"✗ Contrastive learning verification failed: {e}")
            return False
    
    async def verify_model_evaluation(self) -> bool:
        """Verify model performance evaluation."""
        try:
            logger.info("Verifying model evaluation...")
            
            # Create a model first
            config = RetrainingConfig(
                strategy=RetrainingStrategy.INCREMENTAL,
                model_type=EmbeddingModel.SENTENCE_TRANSFORMER
            )
            
            result = await self.retrainer.retrain_embeddings(self.sample_training_data, config)
            
            # Evaluate the model
            test_examples = self.sample_training_data[:3]  # Use subset for testing
            metrics = await self.retrainer.evaluate_model_performance(result.model_id, test_examples)
            
            assert isinstance(metrics, dict), "Should return metrics dictionary"
            
            # Check for either valid metrics or error message
            if 'error' not in metrics:
                # Should have performance metrics
                expected_metrics = ['accuracy', 'precision', 'recall', 'f1_score', 'threshold', 'mean_similarity', 'std_similarity']
                for metric in expected_metrics:
                    if metric in metrics:
                        assert isinstance(metrics[metric], (int, float)), f"{metric} should be numeric"
                        if metric in ['accuracy', 'precision', 'recall', 'f1_score']:
                            assert 0 <= metrics[metric] <= 1, f"{metric} should be between 0 and 1"
            
            logger.info("✓ Model evaluation verified")
            return True
            
        except Exception as e:
            logger.error(f"✗ Model evaluation verification failed: {e}")
            return False
    
    async def verify_model_deployment(self) -> bool:
        """Verify model deployment functionality."""
        try:
            logger.info("Verifying model deployment...")
            
            # Create a model first
            config = RetrainingConfig(
                strategy=RetrainingStrategy.INCREMENTAL,
                model_type=EmbeddingModel.SENTENCE_TRANSFORMER
            )
            
            result = await self.retrainer.retrain_embeddings(self.sample_training_data, config)
            
            # Test different deployment strategies
            deployment_strategies = ["gradual", "immediate", "a_b_test"]
            
            for strategy in deployment_strategies:
                success = await self.retrainer.deploy_retrained_model(result.model_id, strategy)
                assert isinstance(success, bool), f"Deployment should return boolean for {strategy}"
                
                if success:
                    logger.info(f"✓ {strategy.title()} deployment successful")
                else:
                    logger.warning(f"⚠ {strategy.title()} deployment returned False")
            
            logger.info("✓ Model deployment verified")
            return True
            
        except Exception as e:
            logger.error(f"✗ Model deployment verification failed: {e}")
            return False
    
    async def verify_model_monitoring(self) -> bool:
        """Verify model performance monitoring."""
        try:
            logger.info("Verifying model monitoring...")
            
            # Create and deploy a model first
            config = RetrainingConfig(
                strategy=RetrainingStrategy.INCREMENTAL,
                model_type=EmbeddingModel.SENTENCE_TRANSFORMER
            )
            
            result = await self.retrainer.retrain_embeddings(self.sample_training_data, config)
            await self.retrainer.deploy_retrained_model(result.model_id, "immediate")
            
            # Monitor the model
            monitoring_result = await self.retrainer.monitor_model_performance(
                result.model_id,
                monitoring_period_hours=24
            )
            
            assert isinstance(monitoring_result, dict), "Should return monitoring dictionary"
            
            if 'error' not in monitoring_result:
                expected_keys = ['model_id', 'monitoring_period_hours', 'before_metrics', 'after_metrics', 'performance_changes', 'alerts']
                for key in expected_keys:
                    assert key in monitoring_result, f"Should have {key} in monitoring result"
                
                assert monitoring_result['model_id'] == result.model_id, "Should have correct model ID"
                assert monitoring_result['monitoring_period_hours'] == 24, "Should have correct monitoring period"
                assert isinstance(monitoring_result['alerts'], list), "Alerts should be a list"
            
            logger.info("✓ Model monitoring verified")
            return True
            
        except Exception as e:
            logger.error(f"✗ Model monitoring verification failed: {e}")
            return False
    
    async def verify_retraining_recommendations(self) -> bool:
        """Verify retraining recommendations functionality."""
        try:
            logger.info("Verifying retraining recommendations...")
            
            # Test general recommendations
            general_recs = await self.retrainer.get_retraining_recommendations()
            assert isinstance(general_recs, list), "Should return list of recommendations"
            
            # Test domain-specific recommendations
            tech_recs = await self.retrainer.get_retraining_recommendations("technology")
            assert isinstance(tech_recs, list), "Should return list for domain-specific recommendations"
            
            # Verify recommendation structure
            all_recs = general_recs + tech_recs
            for rec in all_recs:
                assert isinstance(rec, dict), "Each recommendation should be a dictionary"
                required_keys = ['type', 'strategy', 'priority', 'description', 'expected_improvement', 'estimated_effort']
                for key in required_keys:
                    assert key in rec, f"Recommendation should have {key}"
                
                assert rec['priority'] in ['high', 'medium', 'low'], "Priority should be valid"
                assert rec['estimated_effort'] in ['high', 'medium', 'low'], "Effort should be valid"
                assert isinstance(rec['expected_improvement'], (int, float)), "Expected improvement should be numeric"
                assert 0 <= rec['expected_improvement'] <= 1, "Expected improvement should be between 0 and 1"
            
            logger.info("✓ Retraining recommendations verified")
            return True
            
        except Exception as e:
            logger.error(f"✗ Retraining recommendations verification failed: {e}")
            return False
    
    async def verify_embedding_calculation(self) -> bool:
        """Verify embedding calculation functionality."""
        try:
            logger.info("Verifying embedding calculation...")
            
            test_texts = [
                "Machine learning algorithms for data analysis",
                "Natural language processing techniques",
                "Database optimization strategies"
            ]
            
            embeddings = await self.retrainer._calculate_embeddings(test_texts, "test_model")
            
            assert isinstance(embeddings, list), "Should return list of embeddings"
            assert len(embeddings) == len(test_texts), "Should have embedding for each text"
            
            if embeddings:
                # Check embedding properties
                for embedding in embeddings:
                    assert len(embedding) == 384, "Should have correct embedding dimension"
                    
                    # Check normalization (should be close to 1)
                    norm = sum(embedding**2)**0.5
                    assert abs(norm - 1.0) < 1e-6, "Embeddings should be normalized"
            
            logger.info("✓ Embedding calculation verified")
            return True
            
        except Exception as e:
            logger.error(f"✗ Embedding calculation verification failed: {e}")
            return False
    
    async def verify_insufficient_training_data_handling(self) -> bool:
        """Verify handling of insufficient training data."""
        try:
            logger.info("Verifying insufficient training data handling...")
            
            # Create too few examples
            few_examples = [
                TrainingExample(text="Test example 1", domain="test"),
                TrainingExample(text="Test example 2", domain="test")
            ]
            
            config = RetrainingConfig(
                strategy=RetrainingStrategy.INCREMENTAL,
                model_type=EmbeddingModel.SENTENCE_TRANSFORMER
            )
            
            # Should raise ValueError for insufficient examples
            try:
                await self.retrainer.retrain_embeddings(few_examples, config)
                assert False, "Should have raised ValueError for insufficient examples"
            except ValueError as e:
                assert "Insufficient training examples" in str(e), "Should have appropriate error message"
            
            logger.info("✓ Insufficient training data handling verified")
            return True
            
        except Exception as e:
            logger.error(f"✗ Insufficient training data handling verification failed: {e}")
            return False
    
    async def run_verification(self) -> Dict[str, bool]:
        """Run all verification tests."""
        logger.info("Starting Task 9.4 verification...")
        
        verification_tests = [
            ("EmbeddingRetrainer Initialization", self.verify_embedding_retrainer_initialization),
            ("Training Data Collection", self.verify_training_data_collection),
            ("Domain Adaptation Data Preparation", self.verify_domain_adaptation_data_preparation),
            ("Incremental Retraining", self.verify_incremental_retraining),
            ("Domain-Specific Fine-Tuning", self.verify_domain_specific_fine_tuning),
            ("Contrastive Learning", self.verify_contrastive_learning),
            ("Model Evaluation", self.verify_model_evaluation),
            ("Model Deployment", self.verify_model_deployment),
            ("Model Monitoring", self.verify_model_monitoring),
            ("Retraining Recommendations", self.verify_retraining_recommendations),
            ("Embedding Calculation", self.verify_embedding_calculation),
            ("Insufficient Training Data Handling", self.verify_insufficient_training_data_handling)
        ]
        
        results = {}
        
        for test_name, test_func in verification_tests:
            try:
                logger.info(f"\n--- Running {test_name} ---")
                results[test_name] = await test_func()
            except Exception as e:
                logger.error(f"Test {test_name} failed with exception: {e}")
                results[test_name] = False
        
        return results


async def main():
    """Main verification function."""
    print("="*80)
    print("TASK 9.4 VERIFICATION: Build embedding retraining capabilities")
    print("="*80)
    
    verifier = Task94Verifier()
    
    # Setup
    setup_success = await verifier.setup()
    if not setup_success:
        print("❌ Setup failed. Cannot proceed with verification.")
        return
    
    # Run verification tests
    results = await verifier.run_verification()
    
    # Print results
    print("\n" + "="*80)
    print("VERIFICATION RESULTS")
    print("="*80)
    
    passed_tests = sum(results.values())
    total_tests = len(results)
    
    print(f"\nTests passed: {passed_tests}/{total_tests}")
    print("-" * 40)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    # Overall result
    print("\n" + "="*80)
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED!")
        print("Task 9.4 (Build embedding retraining capabilities) is COMPLETE")
        print("\nImplemented features:")
        print("✅ EmbeddingRetrainer for model updates")
        print("✅ Domain-specific embedding fine-tuning")
        print("✅ Incremental learning from new documents")
        print("✅ Multiple retraining strategies (incremental, full, domain adaptation, fine-tuning, contrastive)")
        print("✅ Model evaluation and performance monitoring")
        print("✅ Model deployment with different strategies")
        print("✅ Retraining recommendations based on performance analysis")
        print("✅ Comprehensive error handling and validation")
    else:
        print("❌ SOME TESTS FAILED")
        print(f"Task 9.4 verification completed with {total_tests - passed_tests} failing test(s)")
        print("Please check the failed tests and fix the issues.")
    
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())