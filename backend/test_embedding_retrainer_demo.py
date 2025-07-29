#!/usr/bin/env python3
"""
Demo script for EmbeddingRetrainer service.
Tests embedding retraining capabilities including domain-specific fine-tuning and incremental learning.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

from services.embedding_retrainer import (
    EmbeddingRetrainer,
    TrainingExample,
    RetrainingConfig,
    DomainAdaptationData,
    RetrainingStrategy,
    EmbeddingModel
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_sample_training_data() -> List[TrainingExample]:
    """Create sample training data for different domains."""
    
    # Technology domain examples
    tech_examples = [
        TrainingExample(
            text="Machine learning algorithms for predictive analytics",
            domain="technology",
            positive_examples=[
                "Deep learning neural networks for pattern recognition",
                "Statistical models for data prediction",
                "AI algorithms for forecasting"
            ],
            negative_examples=[
                "Cooking recipes for dinner",
                "Sports team statistics",
                "Weather forecast data"
            ],
            metadata={"source": "document", "quality": 0.9, "complexity": "high"}
        ),
        TrainingExample(
            text="Database optimization and query performance",
            domain="technology",
            positive_examples=[
                "SQL query tuning techniques",
                "Index optimization strategies",
                "Database performance monitoring"
            ],
            negative_examples=[
                "Art history timeline",
                "Music composition theory",
                "Literature analysis"
            ],
            metadata={"source": "interaction", "quality": 0.8, "complexity": "medium"}
        ),
        TrainingExample(
            text="Cloud computing infrastructure and scalability",
            domain="technology",
            positive_examples=[
                "AWS services for scalable applications",
                "Kubernetes container orchestration",
                "Microservices architecture patterns"
            ],
            negative_examples=[
                "Traditional cooking methods",
                "Historical events timeline",
                "Fashion trends analysis"
            ],
            metadata={"source": "feedback", "quality": 0.85, "complexity": "high"}
        )
    ]
    
    # Science domain examples
    science_examples = [
        TrainingExample(
            text="Quantum mechanics and particle physics research",
            domain="science",
            positive_examples=[
                "Quantum entanglement experiments",
                "Particle accelerator data analysis",
                "Theoretical physics models"
            ],
            negative_examples=[
                "Business marketing strategies",
                "Social media trends",
                "Entertainment news"
            ],
            metadata={"source": "document", "quality": 0.95, "complexity": "very_high"}
        ),
        TrainingExample(
            text="Climate change and environmental impact studies",
            domain="science",
            positive_examples=[
                "Carbon emission measurements",
                "Global warming trend analysis",
                "Renewable energy research"
            ],
            negative_examples=[
                "Celebrity gossip news",
                "Video game reviews",
                "Restaurant recommendations"
            ],
            metadata={"source": "interaction", "quality": 0.9, "complexity": "high"}
        )
    ]
    
    # Business domain examples
    business_examples = [
        TrainingExample(
            text="Financial market analysis and investment strategies",
            domain="business",
            positive_examples=[
                "Stock market trend analysis",
                "Portfolio optimization techniques",
                "Risk management strategies"
            ],
            negative_examples=[
                "Scientific research papers",
                "Technical documentation",
                "Academic literature"
            ],
            metadata={"source": "document", "quality": 0.8, "complexity": "medium"}
        ),
        TrainingExample(
            text="Supply chain management and logistics optimization",
            domain="business",
            positive_examples=[
                "Inventory management systems",
                "Distribution network optimization",
                "Vendor relationship management"
            ],
            negative_examples=[
                "Poetry and literature",
                "Art criticism",
                "Music theory"
            ],
            metadata={"source": "feedback", "quality": 0.75, "complexity": "medium"}
        )
    ]
    
    return tech_examples + science_examples + business_examples


async def test_training_data_collection(retrainer: EmbeddingRetrainer):
    """Test training data collection functionality."""
    print("\n" + "="*60)
    print("TESTING TRAINING DATA COLLECTION")
    print("="*60)
    
    try:
        # Test general data collection
        print("Testing general training data collection...")
        general_data = await retrainer.collect_training_data(time_window_days=30)
        print(f"✓ Collected {len(general_data)} general training examples")
        
        # Test domain-specific data collection
        print("Testing domain-specific training data collection...")
        tech_data = await retrainer.collect_training_data(domain="technology", time_window_days=30)
        print(f"✓ Collected {len(tech_data)} technology domain examples")
        
        # Display sample data if available
        if general_data:
            sample = general_data[0]
            print(f"Sample training example:")
            print(f"  Text: {sample.text[:100]}...")
            print(f"  Domain: {sample.domain}")
            print(f"  Metadata: {sample.metadata}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error in training data collection: {e}")
        return False


async def test_domain_adaptation(retrainer: EmbeddingRetrainer):
    """Test domain adaptation data preparation."""
    print("\n" + "="*60)
    print("TESTING DOMAIN ADAPTATION")
    print("="*60)
    
    try:
        # Test domain adaptation for technology
        print("Testing technology domain adaptation...")
        tech_adaptation = await retrainer.prepare_domain_adaptation_data("technology")
        
        print(f"✓ Domain: {tech_adaptation.domain_name}")
        print(f"✓ Training examples: {len(tech_adaptation.domain_examples)}")
        print(f"✓ Domain vocabulary: {len(tech_adaptation.domain_vocabulary)} terms")
        print(f"✓ Domain concepts: {len(tech_adaptation.domain_concepts)} concepts")
        print(f"✓ Adaptation weight: {tech_adaptation.adaptation_weight:.3f}")
        
        # Display sample vocabulary and concepts
        if tech_adaptation.domain_vocabulary:
            print(f"Sample vocabulary: {tech_adaptation.domain_vocabulary[:10]}")
        
        if tech_adaptation.domain_concepts:
            print(f"Sample concepts: {tech_adaptation.domain_concepts[:5]}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error in domain adaptation: {e}")
        return False


async def test_retraining_strategies(retrainer: EmbeddingRetrainer, training_examples: List[TrainingExample]):
    """Test different retraining strategies."""
    print("\n" + "="*60)
    print("TESTING RETRAINING STRATEGIES")
    print("="*60)
    
    strategies_to_test = [
        (RetrainingStrategy.INCREMENTAL, "Incremental Learning"),
        (RetrainingStrategy.FULL_RETRAIN, "Full Retraining"),
        (RetrainingStrategy.DOMAIN_ADAPTATION, "Domain Adaptation"),
        (RetrainingStrategy.FINE_TUNING, "Fine-tuning"),
        (RetrainingStrategy.CONTRASTIVE_LEARNING, "Contrastive Learning")
    ]
    
    results = {}
    
    for strategy, strategy_name in strategies_to_test:
        try:
            print(f"\nTesting {strategy_name}...")
            
            config = RetrainingConfig(
                strategy=strategy,
                model_type=EmbeddingModel.SENTENCE_TRANSFORMER,
                learning_rate=1e-5,
                batch_size=16,
                epochs=3
            )
            
            result = await retrainer.retrain_embeddings(training_examples, config)
            results[strategy.value] = result
            
            print(f"✓ Model ID: {result.model_id}")
            print(f"✓ Training Loss: {result.training_loss:.4f}")
            print(f"✓ Validation Loss: {result.validation_loss:.4f}")
            print(f"✓ Improvement Score: {result.improvement_score:.4f}")
            print(f"✓ Training Duration: {result.training_duration:.2f}s")
            print(f"✓ Performance Metrics:")
            for metric, value in result.performance_metrics.items():
                print(f"    {metric}: {value:.4f}")
            
        except Exception as e:
            print(f"✗ Error in {strategy_name}: {e}")
    
    return results


async def test_model_evaluation(retrainer: EmbeddingRetrainer, model_results: Dict[str, Any], test_examples: List[TrainingExample]):
    """Test model performance evaluation."""
    print("\n" + "="*60)
    print("TESTING MODEL EVALUATION")
    print("="*60)
    
    try:
        for strategy, result in model_results.items():
            print(f"\nEvaluating {strategy} model...")
            
            metrics = await retrainer.evaluate_model_performance(
                result.model_id,
                test_examples[:3]  # Use subset for testing
            )
            
            if 'error' in metrics:
                print(f"✗ Evaluation error: {metrics['error']}")
            else:
                print(f"✓ Evaluation completed for {result.model_id}")
                for metric, value in metrics.items():
                    if isinstance(value, (int, float)):
                        print(f"    {metric}: {value:.4f}")
                    else:
                        print(f"    {metric}: {value}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error in model evaluation: {e}")
        return False


async def test_model_deployment(retrainer: EmbeddingRetrainer, model_results: Dict[str, Any]):
    """Test model deployment strategies."""
    print("\n" + "="*60)
    print("TESTING MODEL DEPLOYMENT")
    print("="*60)
    
    deployment_strategies = ["gradual", "immediate", "a_b_test"]
    
    try:
        # Test deployment with the first available model
        if model_results:
            first_result = list(model_results.values())[0]
            
            for strategy in deployment_strategies:
                print(f"\nTesting {strategy} deployment...")
                
                success = await retrainer.deploy_retrained_model(
                    first_result.model_id,
                    strategy
                )
                
                if success:
                    print(f"✓ {strategy.title()} deployment successful")
                else:
                    print(f"✗ {strategy.title()} deployment failed")
        
        return True
        
    except Exception as e:
        print(f"✗ Error in model deployment: {e}")
        return False


async def test_model_monitoring(retrainer: EmbeddingRetrainer, model_results: Dict[str, Any]):
    """Test model performance monitoring."""
    print("\n" + "="*60)
    print("TESTING MODEL MONITORING")
    print("="*60)
    
    try:
        if model_results:
            first_result = list(model_results.values())[0]
            
            print(f"Monitoring model {first_result.model_id}...")
            
            monitoring_result = await retrainer.monitor_model_performance(
                first_result.model_id,
                monitoring_period_hours=24
            )
            
            if 'error' in monitoring_result:
                print(f"✗ Monitoring error: {monitoring_result['error']}")
            else:
                print(f"✓ Monitoring completed")
                print(f"✓ Monitoring period: {monitoring_result['monitoring_period_hours']} hours")
                print(f"✓ Performance changes: {len(monitoring_result['performance_changes'])} metrics")
                print(f"✓ Alerts: {len(monitoring_result['alerts'])} alerts")
                
                # Display alerts if any
                for alert in monitoring_result['alerts']:
                    print(f"    Alert: {alert['type']} in {alert['metric']} ({alert['severity']})")
        
        return True
        
    except Exception as e:
        print(f"✗ Error in model monitoring: {e}")
        return False


async def test_retraining_recommendations(retrainer: EmbeddingRetrainer):
    """Test retraining recommendations."""
    print("\n" + "="*60)
    print("TESTING RETRAINING RECOMMENDATIONS")
    print("="*60)
    
    try:
        # Test general recommendations
        print("Getting general retraining recommendations...")
        general_recs = await retrainer.get_retraining_recommendations()
        
        print(f"✓ Generated {len(general_recs)} general recommendations")
        
        # Test domain-specific recommendations
        print("Getting technology domain recommendations...")
        tech_recs = await retrainer.get_retraining_recommendations("technology")
        
        print(f"✓ Generated {len(tech_recs)} technology recommendations")
        
        # Display recommendations
        all_recs = general_recs + tech_recs
        if all_recs:
            print("\nTop recommendations:")
            for i, rec in enumerate(all_recs[:3], 1):
                print(f"{i}. {rec['type']} ({rec['priority']} priority)")
                print(f"   Strategy: {rec['strategy']}")
                print(f"   Description: {rec['description']}")
                print(f"   Expected improvement: {rec['expected_improvement']:.2f}")
                print(f"   Estimated effort: {rec['estimated_effort']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error in retraining recommendations: {e}")
        return False


async def test_embedding_calculation(retrainer: EmbeddingRetrainer):
    """Test embedding calculation functionality."""
    print("\n" + "="*60)
    print("TESTING EMBEDDING CALCULATION")
    print("="*60)
    
    try:
        test_texts = [
            "Machine learning algorithms for data analysis",
            "Natural language processing techniques",
            "Database optimization strategies",
            "Cloud computing infrastructure"
        ]
        
        print(f"Calculating embeddings for {len(test_texts)} texts...")
        
        embeddings = await retrainer._calculate_embeddings(test_texts, "test_model")
        
        print(f"✓ Generated {len(embeddings)} embeddings")
        print(f"✓ Embedding dimension: {len(embeddings[0]) if embeddings else 0}")
        
        # Test embedding properties
        if embeddings:
            # Check normalization
            norms = [sum(emb**2)**0.5 for emb in embeddings]
            print(f"✓ Embedding norms: {[f'{norm:.3f}' for norm in norms[:3]]}...")
            
            # Check similarity between related texts
            if len(embeddings) >= 2:
                import numpy as np
                similarity = np.dot(embeddings[0], embeddings[1])
                print(f"✓ Similarity between first two texts: {similarity:.3f}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error in embedding calculation: {e}")
        return False


async def main():
    """Main demo function."""
    print("EMBEDDING RETRAINER SERVICE DEMO")
    print("="*60)
    
    # Initialize the embedding retrainer
    retrainer = EmbeddingRetrainer()
    
    try:
        await retrainer.initialize()
        print("✓ EmbeddingRetrainer initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize EmbeddingRetrainer: {e}")
        return
    
    # Create sample training data
    print("\nCreating sample training data...")
    training_examples = await create_sample_training_data()
    print(f"✓ Created {len(training_examples)} training examples")
    
    # Run tests
    test_results = {}
    
    # Test 1: Training data collection
    test_results['data_collection'] = await test_training_data_collection(retrainer)
    
    # Test 2: Domain adaptation
    test_results['domain_adaptation'] = await test_domain_adaptation(retrainer)
    
    # Test 3: Retraining strategies
    model_results = await test_retraining_strategies(retrainer, training_examples)
    test_results['retraining'] = len(model_results) > 0
    
    # Test 4: Model evaluation
    test_results['evaluation'] = await test_model_evaluation(retrainer, model_results, training_examples)
    
    # Test 5: Model deployment
    test_results['deployment'] = await test_model_deployment(retrainer, model_results)
    
    # Test 6: Model monitoring
    test_results['monitoring'] = await test_model_monitoring(retrainer, model_results)
    
    # Test 7: Retraining recommendations
    test_results['recommendations'] = await test_retraining_recommendations(retrainer)
    
    # Test 8: Embedding calculation
    test_results['embeddings'] = await test_embedding_calculation(retrainer)
    
    # Summary
    print("\n" + "="*60)
    print("DEMO SUMMARY")
    print("="*60)
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    print(f"Tests passed: {passed_tests}/{total_tests}")
    
    for test_name, passed in test_results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    if passed_tests == total_tests:
        print("\n🎉 All tests passed! EmbeddingRetrainer is working correctly.")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) failed. Check the output above for details.")
    
    print("\nDemo completed!")


if __name__ == "__main__":
    asyncio.run(main())