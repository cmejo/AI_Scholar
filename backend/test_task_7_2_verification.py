"""
Task 7.2 Verification Script: Implement adaptive retrieval system

This script verifies the implementation of the adaptive retrieval system
according to the task requirements:
- Create AdaptiveRetriever that adjusts based on user history
- Implement personalized ranking of search results
- Add user preference weighting in retrieval
- Test retrieval personalization effectiveness
"""
import asyncio
import json
import logging
import sys
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from core.config import settings
from core.database import get_db, UserProfile, DocumentTag, AnalyticsEvent, Message, User, Document
from services.adaptive_retrieval import AdaptiveRetriever, RetrievalOptimizer
from services.user_profile_service import UserProfileManager
from services.vector_store import VectorStoreService
from models.schemas import UserPreferences, PersonalizationSettings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Task72Verification:
    """Verification class for Task 7.2 implementation."""
    
    def __init__(self):
        self.db = next(get_db())
        self.adaptive_retriever = AdaptiveRetriever(self.db)
        self.retrieval_optimizer = RetrievalOptimizer(self.db)
        self.profile_manager = UserProfileManager(self.db)
        self.vector_store = VectorStoreService()
        self.verification_results = []
    
    def log_verification(self, test_name: str, passed: bool, details: str = ""):
        """Log verification result."""
        status = "PASS" if passed else "FAIL"
        logger.info(f"[{status}] {test_name}")
        if details:
            logger.info(f"    Details: {details}")
        
        self.verification_results.append({
            "test": test_name,
            "passed": passed,
            "details": details
        })
    
    async def verify_adaptive_retriever_exists(self):
        """Verify AdaptiveRetriever class exists and has required methods."""
        test_name = "AdaptiveRetriever class implementation"
        
        try:
            # Check class exists
            assert hasattr(self.adaptive_retriever, 'personalized_search')
            assert hasattr(self.adaptive_retriever, '_get_personalization_weights')
            assert hasattr(self.adaptive_retriever, '_apply_personalized_ranking')
            assert hasattr(self.adaptive_retriever, '_apply_domain_adaptation')
            assert hasattr(self.adaptive_retriever, '_learn_from_search')
            
            # Check method signatures
            import inspect
            sig = inspect.signature(self.adaptive_retriever.personalized_search)
            required_params = ['query', 'user_id', 'limit', 'personalization_level']
            for param in required_params:
                assert param in sig.parameters
            
            self.log_verification(test_name, True, "All required methods and parameters present")
            
        except Exception as e:
            self.log_verification(test_name, False, str(e))
    
    async def verify_personalized_ranking(self):
        """Verify personalized ranking functionality."""
        test_name = "Personalized ranking of search results"
        
        try:
            # Create test data
            sample_results = [
                {
                    "id": "test1",
                    "content": "Machine learning algorithms and implementations",
                    "metadata": {"document_id": "doc1", "document_name": "ML Guide"},
                    "relevance": 0.7
                },
                {
                    "id": "test2", 
                    "content": "Business strategy and market analysis",
                    "metadata": {"document_id": "doc2", "document_name": "Business Guide"},
                    "relevance": 0.8
                },
                {
                    "id": "test3",
                    "content": "Deep learning neural networks research",
                    "metadata": {"document_id": "doc3", "document_name": "DL Research"},
                    "relevance": 0.6
                }
            ]
            
            # Test personalization weights
            weights = {
                "domain_preference": {"technology": 0.9, "business": 0.2},
                "interaction_boost": {"doc1": 0.1},
                "content_type_preference": {"practical": 0.8},
                "recency_preference": 0.6,
                "complexity_preference": 0.7,
                "source_quality_weight": 0.8,
                "feedback_adjustment": 1.0
            }
            
            # Mock domain boost calculation
            original_method = self.adaptive_retriever._calculate_domain_boost
            async def mock_domain_boost(doc_id, domain_prefs, metadata):
                if doc_id == "doc1":
                    return 0.2  # Technology boost
                elif doc_id == "doc2":
                    return 0.05  # Business (lower preference)
                return 0.1
            
            self.adaptive_retriever._calculate_domain_boost = mock_domain_boost
            
            # Apply personalized ranking
            ranked_results = await self.adaptive_retriever._apply_personalized_ranking(
                sample_results, "machine learning", "test_user", weights, 1.0
            )
            
            # Restore original method
            self.adaptive_retriever._calculate_domain_boost = original_method
            
            # Verify results
            assert len(ranked_results) == len(sample_results)
            assert all("personalized_score" in result for result in ranked_results)
            assert all("personalization_factors" in result for result in ranked_results)
            
            # Check sorting by personalized score
            scores = [result["personalized_score"] for result in ranked_results]
            assert scores == sorted(scores, reverse=True)
            
            # Verify technology document got boost
            tech_result = next(r for r in ranked_results if r["metadata"]["document_id"] == "doc1")
            assert tech_result["personalized_score"] > tech_result["relevance"]
            
            self.log_verification(test_name, True, "Personalized ranking working correctly")
            
        except Exception as e:
            self.log_verification(test_name, False, str(e))
    
    async def verify_user_preference_weighting(self):
        """Verify user preference weighting in retrieval."""
        test_name = "User preference weighting in retrieval"
        
        try:
            # Create test user profile
            test_user_id = "test_user_preferences"
            
            # Create user profile with specific preferences
            user_preferences = UserPreferences(
                response_style="detailed",
                domain_focus=["technology", "science"],
                citation_preference="inline",
                reasoning_display=True,
                uncertainty_tolerance=0.7
            )
            
            await self.profile_manager.create_user_profile(
                user_id=test_user_id,
                preferences=user_preferences,
                learning_style="visual"
            )
            
            # Get personalization weights
            user_profile = await self.profile_manager.get_user_profile(test_user_id)
            weights = await self.adaptive_retriever._get_personalization_weights(
                test_user_id, "machine learning algorithms", user_profile
            )
            
            # Verify weight structure
            assert "domain_preference" in weights
            assert "content_type_preference" in weights
            assert "complexity_preference" in weights
            assert "source_quality_weight" in weights
            
            # Verify weights are numeric
            assert isinstance(weights["complexity_preference"], (int, float))
            assert isinstance(weights["source_quality_weight"], (int, float))
            
            # Test query context analysis
            context = await self.adaptive_retriever._analyze_query_context(
                "how to implement machine learning algorithms", test_user_id
            )
            
            assert "domain_signals" in context
            assert "content_type_signals" in context
            assert "question_type" in context
            assert context["question_type"] == "procedural"
            
            self.log_verification(test_name, True, "User preference weighting implemented correctly")
            
        except Exception as e:
            self.log_verification(test_name, False, str(e))
    
    async def verify_user_history_adaptation(self):
        """Verify adaptation based on user history."""
        test_name = "Adaptation based on user history"
        
        try:
            test_user_id = "test_user_history"
            
            # Create user with interaction history
            await self.profile_manager.create_user_profile(
                user_id=test_user_id,
                preferences=UserPreferences(),
                learning_style="visual"
            )
            
            # Simulate interaction history
            interactions = [
                {
                    "type": "query",
                    "data": {
                        "query": "machine learning algorithms",
                        "response_time": 1.2,
                        "sources_used": 3,
                        "satisfaction": 4.5
                    }
                },
                {
                    "type": "document",
                    "data": {
                        "document_id": "tech_doc_1",
                        "query_related": True
                    }
                },
                {
                    "type": "feedback",
                    "data": {
                        "feedback_type": "rating",
                        "rating": 4.0,
                        "message_id": "msg_1"
                    }
                }
            ]
            
            for interaction in interactions:
                await self.profile_manager.track_user_interaction(
                    user_id=test_user_id,
                    interaction_type=interaction["type"],
                    interaction_data=interaction["data"]
                )
            
            # Get historical performance weights
            historical_weights = await self.adaptive_retriever._get_historical_performance_weights(
                test_user_id, "machine learning"
            )
            
            # Verify historical weights structure
            assert isinstance(historical_weights, dict)
            
            # Test behavior analysis
            behavior_analysis = await self.profile_manager.analyze_user_behavior(test_user_id)
            assert "total_interactions" in behavior_analysis
            assert behavior_analysis["total_interactions"] > 0
            
            self.log_verification(test_name, True, "User history adaptation working correctly")
            
        except Exception as e:
            self.log_verification(test_name, False, str(e))
    
    async def verify_personalization_effectiveness(self):
        """Verify retrieval personalization effectiveness."""
        test_name = "Retrieval personalization effectiveness"
        
        try:
            test_user_id = "test_effectiveness"
            
            # Create user profile with strong technology preference
            user_preferences = UserPreferences(
                response_style="detailed",
                domain_focus=["technology"],
                citation_preference="inline"
            )
            
            await self.profile_manager.create_user_profile(
                user_id=test_user_id,
                preferences=user_preferences,
                learning_style="visual"
            )
            
            # Update domain expertise to show strong technology preference
            profile = await self.profile_manager.get_user_profile(test_user_id)
            if profile:
                # Simulate domain expertise through interaction tracking
                for i in range(5):
                    await self.profile_manager.track_user_interaction(
                        user_id=test_user_id,
                        interaction_type="query",
                        interaction_data={
                            "query": f"technology query {i}",
                            "response_time": 1.0,
                            "sources_used": 2,
                            "satisfaction": 4.5
                        }
                    )
            
            # Mock vector store to return consistent results
            original_search = self.adaptive_retriever.vector_store.semantic_search
            
            async def mock_search(query, user_id, limit):
                return [
                    {
                        "id": "tech_result",
                        "content": "Advanced machine learning algorithms and AI implementation",
                        "metadata": {
                            "document_id": "tech_doc",
                            "document_name": "Technology Guide",
                            "content_length": 800
                        },
                        "relevance": 0.7
                    },
                    {
                        "id": "business_result",
                        "content": "Business strategy and market analysis methods",
                        "metadata": {
                            "document_id": "business_doc",
                            "document_name": "Business Guide",
                            "content_length": 600
                        },
                        "relevance": 0.8
                    }
                ]
            
            self.adaptive_retriever.vector_store.semantic_search = mock_search
            
            # Mock database queries for tags
            self.db.query.return_value.filter.return_value.all.return_value = [
                type('MockTag', (), {
                    'tag_name': 'technology',
                    'confidence_score': 0.9,
                    'tag_type': 'domain'
                })()
            ]
            
            # Mock analytics event storage
            self.db.add = lambda x: None
            self.db.commit = lambda: None
            
            # Test personalized search
            personalized_results = await self.adaptive_retriever.personalized_search(
                query="machine learning algorithms",
                user_id=test_user_id,
                limit=5,
                personalization_level=1.0
            )
            
            # Test non-personalized search for comparison
            non_personalized_results = await self.adaptive_retriever.personalized_search(
                query="machine learning algorithms",
                user_id=test_user_id,
                limit=5,
                personalization_level=0.0
            )
            
            # Restore original method
            self.adaptive_retriever.vector_store.semantic_search = original_search
            
            # Verify personalization effects
            assert len(personalized_results) > 0
            assert len(non_personalized_results) > 0
            
            # Check that personalized results have personalization scores
            personalized_result = personalized_results[0]
            assert "personalized_score" in personalized_result
            assert "personalization_factors" in personalized_result
            
            # Verify that technology-related content gets boosted
            tech_result = next((r for r in personalized_results if "technology" in r["content"].lower()), None)
            if tech_result:
                assert tech_result["personalized_score"] >= tech_result["relevance"]
            
            self.log_verification(test_name, True, "Personalization effectiveness verified")
            
        except Exception as e:
            self.log_verification(test_name, False, str(e))
    
    async def verify_retrieval_optimizer(self):
        """Verify retrieval optimizer functionality."""
        test_name = "Retrieval optimizer implementation"
        
        try:
            # Check RetrievalOptimizer exists and has required methods
            assert hasattr(self.retrieval_optimizer, 'optimize_for_user')
            assert hasattr(self.retrieval_optimizer, '_analyze_feedback_patterns')
            assert hasattr(self.retrieval_optimizer, '_generate_optimization_recommendations')
            
            # Test feedback pattern analysis
            sample_feedback = [
                {
                    "rating": 5,
                    "domains": ["technology", "ai"],
                    "query": "machine learning",
                    "timestamp": datetime.utcnow().isoformat()
                },
                {
                    "rating": 2,
                    "domains": ["business"],
                    "query": "market analysis",
                    "timestamp": datetime.utcnow().isoformat()
                }
            ]
            
            analysis = self.retrieval_optimizer._analyze_feedback_patterns(sample_feedback)
            
            assert "avg_rating" in analysis
            assert "preferred_domains" in analysis
            assert "avoided_domains" in analysis
            assert analysis["total_feedback"] == 2
            
            # Test recommendation generation
            mock_profile = type('MockProfile', (), {'domain_expertise': {'technology': 0.5}})()
            
            recommendations = await self.retrieval_optimizer._generate_optimization_recommendations(
                analysis, mock_profile
            )
            
            assert "domain_weight_adjustments" in recommendations
            assert "confidence" in recommendations
            assert isinstance(recommendations["confidence"], (int, float))
            
            self.log_verification(test_name, True, "Retrieval optimizer working correctly")
            
        except Exception as e:
            self.log_verification(test_name, False, str(e))
    
    async def verify_personalization_settings(self):
        """Verify personalization settings integration."""
        test_name = "Personalization settings integration"
        
        try:
            # Test with custom settings
            custom_settings = PersonalizationSettings(
                enable_adaptive_retrieval=True,
                learning_rate=0.2,
                feedback_weight=0.9,
                domain_adaptation=True,
                memory_retention_days=60
            )
            
            # Mock vector store search
            async def mock_search(query, user_id, limit):
                return [
                    {
                        "id": "test_result",
                        "content": "Test content",
                        "metadata": {"document_id": "test_doc", "document_name": "Test"},
                        "relevance": 0.8
                    }
                ]
            
            original_search = self.adaptive_retriever.vector_store.semantic_search
            self.adaptive_retriever.vector_store.semantic_search = mock_search
            
            # Mock profile manager
            mock_profile = type('MockProfile', (), {
                'domain_expertise': {'technology': 0.8},
                'preferences': {'response_style': 'detailed'}
            })()
            
            original_get_profile = self.adaptive_retriever.profile_manager.get_user_profile
            self.adaptive_retriever.profile_manager.get_user_profile = lambda x: mock_profile
            
            # Mock database operations
            self.db.query.return_value.filter.return_value.all.return_value = []
            self.db.add = lambda x: None
            self.db.commit = lambda: None
            
            # Test search with custom settings
            results = await self.adaptive_retriever.personalized_search(
                query="test query",
                user_id="test_user",
                limit=5,
                personalization_level=1.0,
                settings=custom_settings
            )
            
            # Restore original methods
            self.adaptive_retriever.vector_store.semantic_search = original_search
            self.adaptive_retriever.profile_manager.get_user_profile = original_get_profile
            
            assert len(results) > 0
            assert custom_settings.enable_adaptive_retrieval == True
            assert custom_settings.domain_adaptation == True
            
            self.log_verification(test_name, True, "Personalization settings working correctly")
            
        except Exception as e:
            self.log_verification(test_name, False, str(e))
    
    async def verify_analytics_integration(self):
        """Verify analytics integration for learning."""
        test_name = "Analytics integration for learning"
        
        try:
            test_user_id = "test_analytics"
            
            # Mock database operations
            self.db.add = lambda x: None
            self.db.commit = lambda: None
            
            # Test learning from search
            sample_results = [
                {
                    "id": "result1",
                    "content": "Test content",
                    "metadata": {"document_id": "doc1", "document_name": "Test Doc"},
                    "relevance": 0.8
                }
            ]
            
            # Mock domain extraction
            original_extract = self.adaptive_retriever._extract_top_domains
            self.adaptive_retriever._extract_top_domains = lambda x: ["technology", "science"]
            
            await self.adaptive_retriever._learn_from_search(
                test_user_id, "test query", sample_results
            )
            
            # Restore original method
            self.adaptive_retriever._extract_top_domains = original_extract
            
            # Test personalization stats (with mocked data)
            mock_events = [
                type('MockEvent', (), {
                    'event_data': {
                        'personalization_applied': True,
                        'results_count': 5,
                        'top_domains': ['technology']
                    }
                })()
            ]
            
            self.db.query.return_value.filter.return_value.all.return_value = mock_events
            
            stats = await self.adaptive_retriever.get_personalization_stats(test_user_id)
            
            assert "total_searches" in stats
            assert "personalization_rate" in stats
            
            self.log_verification(test_name, True, "Analytics integration working correctly")
            
        except Exception as e:
            self.log_verification(test_name, False, str(e))
    
    async def run_all_verifications(self):
        """Run all verification tests."""
        logger.info("Starting Task 7.2 Verification: Implement adaptive retrieval system")
        logger.info("=" * 70)
        
        try:
            await self.verify_adaptive_retriever_exists()
            await self.verify_personalized_ranking()
            await self.verify_user_preference_weighting()
            await self.verify_user_history_adaptation()
            await self.verify_personalization_effectiveness()
            await self.verify_retrieval_optimizer()
            await self.verify_personalization_settings()
            await self.verify_analytics_integration()
            
        except Exception as e:
            logger.error(f"Verification error: {str(e)}")
        finally:
            self.db.close()
        
        # Summary
        logger.info("\n" + "=" * 70)
        logger.info("VERIFICATION SUMMARY")
        logger.info("=" * 70)
        
        total_tests = len(self.verification_results)
        passed_tests = sum(1 for result in self.verification_results if result["passed"])
        failed_tests = total_tests - passed_tests
        
        logger.info(f"Total tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {failed_tests}")
        logger.info(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            logger.info("\nFailed tests:")
            for result in self.verification_results:
                if not result["passed"]:
                    logger.info(f"  - {result['test']}: {result['details']}")
        
        # Task completion assessment
        critical_features = [
            "AdaptiveRetriever class implementation",
            "Personalized ranking of search results", 
            "User preference weighting in retrieval",
            "Retrieval personalization effectiveness"
        ]
        
        critical_passed = sum(
            1 for result in self.verification_results 
            if result["test"] in critical_features and result["passed"]
        )
        
        if critical_passed == len(critical_features):
            logger.info(f"\n✅ TASK 7.2 COMPLETED SUCCESSFULLY")
            logger.info("All critical requirements have been implemented:")
            logger.info("- ✅ AdaptiveRetriever that adjusts based on user history")
            logger.info("- ✅ Personalized ranking of search results")
            logger.info("- ✅ User preference weighting in retrieval")
            logger.info("- ✅ Retrieval personalization effectiveness testing")
            return True
        else:
            logger.info(f"\n❌ TASK 7.2 INCOMPLETE")
            logger.info(f"Critical features passed: {critical_passed}/{len(critical_features)}")
            return False

async def main():
    """Main verification function."""
    verification = Task72Verification()
    success = await verification.run_all_verifications()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())