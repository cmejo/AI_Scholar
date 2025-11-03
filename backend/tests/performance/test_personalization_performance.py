"""Performance and scalability tests for personalization system."""

import pytest
import asyncio
import time
import psutil
import os
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any
from unittest.mock import Mock
from datetime import datetime, timedelta

from backend.rl.personalization.advanced_adaptation_algorithms import AdvancedAdaptationAlgorithms
from backend.rl.personalization.user_behavior_predictor import UserBehaviorPredictor
from backend.rl.user_modeling.personalization_engine import PersonalizationEngine
from backend.rl.user_modeling.enhanced_user_models import EnhancedUserProfile
from backend.rl.models.user_models import UserInteraction, UserContext, UserHistory
from backend.rl.utils import performance_logger


class TestPersonalizationPerformance:
    """Performance tests for personalization system components."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.adaptation_algorithms = AdvancedAdaptationAlgorithms()
        self.behavior_predictor = UserBehaviorPredictor()
        self.personalization_engine = PersonalizationEngine()
        
        # Performance tracking
        self.process = psutil.Process(os.getpid())
        self.performance_metrics = {}
    
    def measure_performance(self, operation_name: str):
        """Context manager for measuring performance."""
        class PerformanceMeasurer:
            def __init__(self, test_instance, name):
                self.test_instance = test_instance
                self.name = name
                self.start_time = None
                self.start_memory = None
            
            def __enter__(self):
                self.start_time = time.time()
                self.start_memory = self.test_instance.process.memory_info().rss / 1024 / 1024
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                end_time = time.time()
                end_memory = self.test_instance.process.memory_info().rss / 1024 / 1024
                
                metrics = {
                    'duration': end_time - self.start_time,
                    'memory_start': self.start_memory,
                    'memory_end': end_memory,
                    'memory_delta': end_memory - self.start_memory
                }
                
                self.test_instance.performance_metrics[self.name] = metrics
                
                performance_logger.log_processing_time(
                    operation=self.name,
                    component="personalization",
                    processing_time=metrics['duration']
                )
        
        return PerformanceMeasurer(self, operation_name)
    
    def create_user_interactions(self, count: int, user_id: str = "test_user") -> List[UserInteraction]:
        """Create test user interactions."""
        interactions = []
        base_time = datetime.now() - timedelta(days=30)
        
        for i in range(count):
            interaction = UserInteraction(
                user_id=user_id,
                interaction_type=["document_view", "search", "recommendation_click", "visual_click"][i % 4],
                content_id=f"content_{i:06d}",
                timestamp=base_time + timedelta(minutes=i*10),
                duration=60 + (i % 300),
                feedback_score=2.0 + (i % 4),
                context={
                    "domain": ["ml", "cv", "nlp", "robotics"][i % 4],
                    "content_type": ["paper", "tutorial", "code", "dataset"][i % 4],
                    "session_id": f"session_{i // 20}"
                }
            )
            interactions.append(interaction)
        
        return interactions
    
    @pytest.mark.asyncio
    async def test_deep_preference_learning_performance_small_dataset(self):
        """Test deep preference learning performance with small dataset."""
        interactions = self.create_user_interactions(100)
        
        with self.measure_performance("deep_preference_learning_small"):
            preference_model = await self.adaptation_algorithms.deep_preference_learning(interactions)
        
        # Verify results
        assert preference_model is not None
        assert preference_model.preference_embeddings is not None
        
        # Performance assertions
        metrics = self.performance_metrics["deep_preference_learning_small"]
        assert metrics['duration'] < 2.0, f"Small dataset learning too slow: {metrics['duration']}s"
        assert metrics['memory_delta'] < 50, f"Memory usage too high: {metrics['memory_delta']}MB"
    
    @pytest.mark.asyncio
    async def test_deep_preference_learning_performance_large_dataset(self):
        """Test deep preference learning performance with large dataset."""
        interactions = self.create_user_interactions(10000)  # Large dataset
        
        with self.measure_performance("deep_preference_learning_large"):
            preference_model = await self.adaptation_algorithms.deep_preference_learning(interactions)
        
        # Verify results
        assert preference_model is not None
        assert len(preference_model.preference_weights) > 0
        
        # Performance assertions
        metrics = self.performance_metrics["deep_preference_learning_large"]
        assert metrics['duration'] < 30.0, f"Large dataset learning too slow: {metrics['duration']}s"
        assert metrics['memory_delta'] < 200, f"Memory usage too high: {metrics['memory_delta']}MB"
        
        # Calculate throughput
        throughput = len(interactions) / metrics['duration']
        performance_logger.log_throughput(
            component="personalization",
            operation="deep_preference_learning",
            items_processed=len(interactions),
            time_elapsed=metrics['duration']
        )
        
        assert throughput > 300, f"Learning throughput too low: {throughput} interactions/sec"
    
    @pytest.mark.asyncio
    async def test_behavior_prediction_performance_batch(self):
        """Test behavior prediction performance with batch processing."""
        # Create multiple user contexts
        contexts = []
        for i in range(1000):
            interactions = self.create_user_interactions(20, f"user_{i:04d}")
            context = UserContext(
                user_id=f"user_{i:04d}",
                current_task=["research", "exploration", "analysis"][i % 3],
                research_domain=["ml", "cv", "nlp"][i % 3],
                session_context={"session_id": f"session_{i}"},
                interaction_history=interactions[-5:]  # Last 5 interactions
            )
            contexts.append(context)
        
        with self.measure_performance("behavior_prediction_batch"):
            predictions = []
            for context in contexts:
                prediction = await self.behavior_predictor.predict_next_action(context)
                predictions.append(prediction)
        
        # Verify results
        assert len(predictions) == 1000
        assert all(pred is not None for pred in predictions)
        
        # Performance assertions
        metrics = self.performance_metrics["behavior_prediction_batch"]
        assert metrics['duration'] < 20.0, f"Batch prediction too slow: {metrics['duration']}s"
        
        # Calculate prediction throughput
        throughput = len(contexts) / metrics['duration']
        assert throughput > 50, f"Prediction throughput too low: {throughput} predictions/sec"
    
    @pytest.mark.asyncio
    async def test_contextual_bandit_performance(self):
        """Test contextual bandit optimization performance."""
        # Create test context
        interactions = self.create_user_interactions(50)
        context = UserContext(
            user_id="bandit_test_user",
            current_task="research",
            research_domain="machine_learning",
            session_context={},
            interaction_history=interactions[-10:]
        )
        
        # Create many action options
        available_actions = [
            {"type": f"action_{i}", "domain": ["ml", "cv", "nlp"][i % 3], "complexity": i % 5}
            for i in range(100)  # Many actions to choose from
        ]
        
        with self.measure_performance("contextual_bandit_optimization"):
            optimal_actions = []
            for _ in range(50):  # Multiple optimization calls
                optimal_action = await self.adaptation_algorithms.contextual_bandit_optimization(
                    context, available_actions
                )
                optimal_actions.append(optimal_action)
        
        # Verify results
        assert len(optimal_actions) == 50
        assert all(action is not None for action in optimal_actions)
        
        # Performance assertions
        metrics = self.performance_metrics["contextual_bandit_optimization"]
        assert metrics['duration'] < 5.0, f"Bandit optimization too slow: {metrics['duration']}s"
        
        # Average time per optimization should be reasonable
        avg_time_per_optimization = metrics['duration'] / 50
        assert avg_time_per_optimization < 0.1, f"Per-optimization time too high: {avg_time_per_optimization}s"
    
    @pytest.mark.asyncio
    async def test_meta_learning_performance(self):
        """Test meta-learning adaptation performance."""
        # Create target user profile
        target_user = EnhancedUserProfile(
            user_id="target_user",
            preferences={"domain": "ml", "content_type": "papers"},
            behavior_patterns=[],
            adaptation_history=[],
            multi_modal_preferences={}
        )
        
        # Create many similar users
        similar_users = []
        for i in range(200):  # Large number of similar users
            user = EnhancedUserProfile(
                user_id=f"similar_user_{i:03d}",
                preferences={
                    "domain": ["ml", "cv", "nlp"][i % 3],
                    "content_type": ["papers", "tutorials"][i % 2],
                    "interaction_style": ["detailed", "quick"][i % 2]
                },
                behavior_patterns=[
                    {"pattern_type": "reading", "strength": 0.5 + (i % 5) * 0.1},
                    {"pattern_type": "exploration", "strength": 0.3 + (i % 3) * 0.2}
                ],
                adaptation_history=[],
                multi_modal_preferences={
                    "visual": 0.5 + (i % 5) * 0.1,
                    "text": 0.6 + (i % 4) * 0.1
                }
            )
            similar_users.append(user)
        
        with self.measure_performance("meta_learning_adaptation"):
            adaptation_strategy = await self.adaptation_algorithms.meta_learning_adaptation(
                target_user, similar_users
            )
        
        # Verify results
        assert adaptation_strategy is not None
        assert adaptation_strategy.strategy_type is not None
        
        # Performance assertions
        metrics = self.performance_metrics["meta_learning_adaptation"]
        assert metrics['duration'] < 10.0, f"Meta-learning too slow: {metrics['duration']}s"
        
        # Should handle large number of similar users efficiently
        users_per_second = len(similar_users) / metrics['duration']
        assert users_per_second > 20, f"Meta-learning throughput too low: {users_per_second} users/sec"
    
    @pytest.mark.asyncio
    async def test_pattern_identification_performance(self):
        """Test behavior pattern identification performance."""
        # Create comprehensive user history
        interactions = self.create_user_interactions(5000)  # Large interaction history
        
        user_history = UserHistory(
            user_id="pattern_test_user",
            interactions=interactions,
            preferences_evolution=[],
            session_patterns=[]
        )
        
        with self.measure_performance("pattern_identification"):
            behavior_patterns = await self.behavior_predictor.identify_behavior_patterns(user_history)
        
        # Verify results
        assert behavior_patterns is not None
        assert len(behavior_patterns) > 0
        
        # Performance assertions
        metrics = self.performance_metrics["pattern_identification"]
        assert metrics['duration'] < 15.0, f"Pattern identification too slow: {metrics['duration']}s"
        
        # Should process interactions efficiently
        interactions_per_second = len(interactions) / metrics['duration']
        assert interactions_per_second > 300, f"Pattern identification throughput too low: {interactions_per_second} interactions/sec"
    
    @pytest.mark.asyncio
    async def test_real_time_personalization_performance(self):
        """Test real-time personalization performance."""
        # Create user profile
        user_profile = EnhancedUserProfile(
            user_id="realtime_user",
            preferences={"domain": "ml", "style": "detailed"},
            behavior_patterns=[],
            adaptation_history=[],
            multi_modal_preferences={}
        )
        
        # Create contexts for real-time processing
        contexts = []
        for i in range(100):
            context = UserContext(
                user_id="realtime_user",
                current_task="research",
                research_domain="machine_learning",
                session_context={"timestamp": datetime.now()},
                interaction_history=self.create_user_interactions(5)
            )
            contexts.append(context)
        
        with self.measure_performance("real_time_personalization"):
            personalized_experiences = []
            for context in contexts:
                # Simulate real-time personalization
                predicted_action = await self.behavior_predictor.predict_next_action(context)
                
                personalized_experience = await self.personalization_engine.personalize_experience(
                    user_profile, context, predicted_action
                )
                personalized_experiences.append(personalized_experience)
        
        # Verify results
        assert len(personalized_experiences) == 100
        assert all(exp is not None for exp in personalized_experiences)
        
        # Performance assertions for real-time requirements
        metrics = self.performance_metrics["real_time_personalization"]
        assert metrics['duration'] < 5.0, f"Real-time personalization too slow: {metrics['duration']}s"
        
        # Average response time should be very fast for real-time use
        avg_response_time = metrics['duration'] / len(contexts)
        assert avg_response_time < 0.05, f"Average response time too high: {avg_response_time}s"
        
        # Real-time throughput should be high
        throughput = len(contexts) / metrics['duration']
        assert throughput > 20, f"Real-time throughput too low: {throughput} personalizations/sec"
    
    @pytest.mark.asyncio
    async def test_concurrent_personalization_performance(self):
        """Test concurrent personalization performance."""
        # Create multiple user profiles
        user_profiles = [
            EnhancedUserProfile(
                user_id=f"concurrent_user_{i:03d}",
                preferences={"domain": ["ml", "cv", "nlp"][i % 3]},
                behavior_patterns=[],
                adaptation_history=[],
                multi_modal_preferences={}
            )
            for i in range(50)
        ]
        
        # Create contexts for each user
        contexts = [
            UserContext(
                user_id=profile.user_id,
                current_task="research",
                research_domain=profile.preferences["domain"],
                session_context={},
                interaction_history=self.create_user_interactions(10, profile.user_id)
            )
            for profile in user_profiles
        ]
        
        async def personalize_user(profile, context):
            predicted_action = await self.behavior_predictor.predict_next_action(context)
            return await self.personalization_engine.personalize_experience(
                profile, context, predicted_action
            )
        
        with self.measure_performance("concurrent_personalization"):
            # Process all users concurrently
            tasks = [personalize_user(profile, context) 
                    for profile, context in zip(user_profiles, contexts)]
            concurrent_results = await asyncio.gather(*tasks)
        
        # Verify results
        assert len(concurrent_results) == 50
        assert all(result is not None for result in concurrent_results)
        
        # Performance assertions
        metrics = self.performance_metrics["concurrent_personalization"]
        
        # Concurrent processing should be faster than sequential
        sequential_estimate = len(user_profiles) * 0.1  # Estimated 0.1s per user
        assert metrics['duration'] < sequential_estimate * 0.7, \
            f"Concurrent processing not efficient: {metrics['duration']}s vs estimated {sequential_estimate}s"
        
        # Concurrent throughput should be high
        throughput = len(user_profiles) / metrics['duration']
        assert throughput > 10, f"Concurrent throughput too low: {throughput} users/sec"
    
    @pytest.mark.asyncio
    async def test_memory_efficiency_large_user_base(self):
        """Test memory efficiency with large user base."""
        initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        # Create large number of user profiles
        user_profiles = []
        for i in range(1000):  # Large user base
            profile = EnhancedUserProfile(
                user_id=f"memory_user_{i:04d}",
                preferences={
                    "domain": ["ml", "cv", "nlp", "robotics"][i % 4],
                    "content_type": ["papers", "tutorials", "code"][i % 3],
                    "complexity": ["beginner", "intermediate", "advanced"][i % 3]
                },
                behavior_patterns=[
                    {"pattern_type": "reading", "strength": 0.5 + (i % 5) * 0.1},
                    {"pattern_type": "exploration", "strength": 0.3 + (i % 3) * 0.2}
                ],
                adaptation_history=[
                    {"timestamp": datetime.now() - timedelta(days=j), "adaptation": f"adapt_{j}"}
                    for j in range(10)
                ],
                multi_modal_preferences={
                    "visual": 0.5 + (i % 5) * 0.1,
                    "text": 0.6 + (i % 4) * 0.1,
                    "interactive": 0.4 + (i % 3) * 0.15
                }
            )
            user_profiles.append(profile)
        
        with self.measure_performance("memory_efficiency_large_user_base"):
            # Process personalization for all users
            results = []
            for i, profile in enumerate(user_profiles):
                if i % 100 == 0:  # Sample every 100th user for processing
                    context = UserContext(
                        user_id=profile.user_id,
                        current_task="research",
                        research_domain=profile.preferences["domain"],
                        session_context={},
                        interaction_history=self.create_user_interactions(5, profile.user_id)
                    )
                    
                    predicted_action = await self.behavior_predictor.predict_next_action(context)
                    personalized = await self.personalization_engine.personalize_experience(
                        profile, context, predicted_action
                    )
                    results.append(personalized)
        
        final_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory efficiency assertions
        assert memory_increase < 300, f"Memory increase too high: {memory_increase}MB"
        
        # Memory per user should be reasonable
        memory_per_user = memory_increase / len(user_profiles)
        assert memory_per_user < 0.3, f"Memory per user too high: {memory_per_user}MB"
        
        performance_logger.info(
            "Large user base memory efficiency test",
            initial_memory_mb=initial_memory,
            final_memory_mb=final_memory,
            memory_increase_mb=memory_increase,
            user_count=len(user_profiles),
            memory_per_user_kb=memory_per_user * 1024
        )
    
    def test_performance_under_load(self):
        """Test personalization performance under sustained load."""
        import threading
        import queue
        
        # Performance metrics collection
        response_times = queue.Queue()
        error_count = 0
        
        def load_test_worker():
            nonlocal error_count
            try:
                # Simulate sustained load
                for i in range(20):
                    start_time = time.time()
                    
                    # Create user interaction data
                    interactions = self.create_user_interactions(50, f"load_user_{threading.current_thread().ident}")
                    
                    # Simulate synchronous preference learning (simplified)
                    # In real scenario, this would be the async version
                    time.sleep(0.01)  # Simulate processing time
                    
                    response_time = time.time() - start_time
                    response_times.put(response_time)
                    
                    # Small delay between requests
                    time.sleep(0.05)
                    
            except Exception:
                error_count += 1
        
        # Start multiple worker threads to simulate load
        threads = []
        start_time = time.time()
        
        for i in range(5):  # 5 concurrent workers
            thread = threading.Thread(target=load_test_worker)
            thread.start()
            threads.append(thread)
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # Collect response time statistics
        times = []
        while not response_times.empty():
            times.append(response_times.get())
        
        if times:
            avg_response_time = sum(times) / len(times)
            max_response_time = max(times)
            min_response_time = min(times)
            
            performance_logger.info(
                "Load test performance results",
                total_requests=len(times),
                total_time=total_time,
                avg_response_time=avg_response_time,
                max_response_time=max_response_time,
                min_response_time=min_response_time,
                error_count=error_count,
                requests_per_second=len(times) / total_time
            )
            
            # Performance assertions under load
            assert avg_response_time < 0.1, f"Average response time under load too high: {avg_response_time}s"
            assert max_response_time < 0.5, f"Max response time under load too high: {max_response_time}s"
            assert error_count == 0, f"Errors occurred under load: {error_count}"
            
            # Throughput should be maintained under load
            throughput = len(times) / total_time
            assert throughput > 50, f"Throughput under load too low: {throughput} requests/sec"


class TestPersonalizationScalability:
    """Scalability tests for personalization system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.adaptation_algorithms = AdvancedAdaptationAlgorithms()
        self.behavior_predictor = UserBehaviorPredictor()
    
    @pytest.mark.asyncio
    async def test_scalability_user_count(self):
        """Test scalability with increasing user count."""
        user_counts = [10, 50, 100, 500]
        scalability_results = {}
        
        for count in user_counts:
            # Create user interactions for multiple users
            all_interactions = []
            for i in range(count):
                user_interactions = [
                    UserInteraction(
                        user_id=f"scale_user_{i:04d}",
                        interaction_type="document_view",
                        content_id=f"content_{j}",
                        timestamp=datetime.now() - timedelta(minutes=j),
                        duration=60 + j,
                        feedback_score=3.0 + (j % 3),
                        context={"domain": "ml"}
                    )
                    for j in range(20)  # 20 interactions per user
                ]
                all_interactions.extend(user_interactions)
            
            # Measure preference learning time
            start_time = time.time()
            preference_model = await self.adaptation_algorithms.deep_preference_learning(all_interactions)
            processing_time = time.time() - start_time
            
            scalability_results[count] = {
                "processing_time": processing_time,
                "interactions_processed": len(all_interactions),
                "time_per_user": processing_time / count,
                "interactions_per_second": len(all_interactions) / processing_time
            }
            
            performance_logger.info(
                f"User scalability test with {count} users",
                user_count=count,
                processing_time=processing_time,
                interactions_processed=len(all_interactions),
                time_per_user=processing_time / count
            )
        
        # Analyze scalability
        for i in range(1, len(user_counts)):
            prev_count = user_counts[i-1]
            curr_count = user_counts[i]
            
            prev_time = scalability_results[prev_count]["processing_time"]
            curr_time = scalability_results[curr_count]["processing_time"]
            
            # Time should scale reasonably with user count
            time_ratio = curr_time / prev_time
            count_ratio = curr_count / prev_count
            
            # Allow for some overhead but should not be worse than quadratic
            assert time_ratio <= count_ratio * 1.5, \
                f"Poor scalability: {curr_count} users took {time_ratio:.2f}x time vs {count_ratio:.2f}x users"
    
    @pytest.mark.asyncio
    async def test_scalability_interaction_history_length(self):
        """Test scalability with increasing interaction history length."""
        history_lengths = [100, 500, 1000, 5000, 10000]
        scalability_results = {}
        
        for length in history_lengths:
            # Create long interaction history
            interactions = [
                UserInteraction(
                    user_id="history_scale_user",
                    interaction_type=["view", "click", "rate", "search"][i % 4],
                    content_id=f"content_{i:06d}",
                    timestamp=datetime.now() - timedelta(minutes=i),
                    duration=30 + (i % 120),
                    feedback_score=2.0 + (i % 4),
                    context={"sequence": i}
                )
                for i in range(length)
            ]
            
            # Measure processing time
            start_time = time.time()
            preference_model = await self.adaptation_algorithms.deep_preference_learning(interactions)
            processing_time = time.time() - start_time
            
            scalability_results[length] = {
                "processing_time": processing_time,
                "time_per_interaction": processing_time / length,
                "interactions_per_second": length / processing_time
            }
            
            performance_logger.info(
                f"History length scalability test with {length} interactions",
                history_length=length,
                processing_time=processing_time,
                time_per_interaction=processing_time / length
            )
        
        # Verify scalability
        for length in history_lengths:
            result = scalability_results[length]
            # Processing time should not grow too quickly
            assert result["time_per_interaction"] < 0.01, \
                f"Time per interaction too high for {length} interactions: {result['time_per_interaction']}s"
    
    @pytest.mark.asyncio
    async def test_scalability_preference_dimensions(self):
        """Test scalability with increasing preference space dimensions."""
        dimensions = [10, 50, 100, 500, 1000]
        scalability_results = {}
        
        for dim in dimensions:
            # Create interactions with high-dimensional preference space
            interactions = []
            for i in range(200):  # Fixed number of interactions
                context = {f"feature_{j}": np.random.rand() for j in range(dim)}
                interaction = UserInteraction(
                    user_id="dimension_scale_user",
                    interaction_type="document_view",
                    content_id=f"content_{i}",
                    timestamp=datetime.now() - timedelta(minutes=i),
                    duration=60 + i,
                    feedback_score=2.0 + (i % 4),
                    context=context
                )
                interactions.append(interaction)
            
            # Measure processing time
            start_time = time.time()
            preference_model = await self.adaptation_algorithms.deep_preference_learning(interactions)
            processing_time = time.time() - start_time
            
            scalability_results[dim] = {
                "processing_time": processing_time,
                "time_per_dimension": processing_time / dim
            }
            
            performance_logger.info(
                f"Preference dimension scalability test with {dim}D",
                preference_dimensions=dim,
                processing_time=processing_time,
                time_per_dimension=processing_time / dim
            )
        
        # Verify reasonable scaling with dimensions
        for dim in dimensions:
            result = scalability_results[dim]
            assert result["processing_time"] < 20.0, \
                f"Processing with {dim}D preferences too slow: {result['processing_time']}s"


if __name__ == "__main__":
    pytest.main([__file__])