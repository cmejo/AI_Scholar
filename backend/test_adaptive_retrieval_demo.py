"""
Demo script for Adaptive Retrieval System

This script demonstrates the personalized search capabilities,
ranking algorithms, and optimization features of the adaptive retrieval system.
"""
import asyncio
import json
import logging
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

class AdaptiveRetrievalDemo:
    """Demo class for adaptive retrieval system."""
    
    def __init__(self):
        self.db = next(get_db())
        self.adaptive_retriever = AdaptiveRetriever(self.db)
        self.retrieval_optimizer = RetrievalOptimizer(self.db)
        self.profile_manager = UserProfileManager(self.db)
        self.vector_store = VectorStoreService()
    
    async def setup_demo_data(self):
        """Set up demo data for testing."""
        logger.info("Setting up demo data...")
        
        try:
            # Initialize vector store
            await self.vector_store.initialize()
            
            # Create demo user if not exists
            demo_user = self.db.query(User).filter(User.email == "demo@adaptive.test").first()
            if not demo_user:
                demo_user = User(
                    email="demo@adaptive.test",
                    name="Demo User",
                    password_hash="demo_hash"
                )
                self.db.add(demo_user)
                self.db.commit()
                self.db.refresh(demo_user)
            
            self.demo_user_id = demo_user.id
            
            # Create user profile with preferences
            user_preferences = UserPreferences(
                response_style="detailed",
                domain_focus=["technology", "science"],
                citation_preference="inline",
                reasoning_display=True,
                uncertainty_tolerance=0.6
            )
            
            await self.profile_manager.create_user_profile(
                user_id=self.demo_user_id,
                preferences=user_preferences,
                learning_style="visual"
            )
            
            # Create demo documents and tags
            await self._create_demo_documents()
            
            # Create demo interaction history
            await self._create_demo_interactions()
            
            logger.info("Demo data setup completed")
            
        except Exception as e:
            logger.error(f"Error setting up demo data: {str(e)}")
            self.db.rollback()
            raise
    
    async def _create_demo_documents(self):
        """Create demo documents with tags."""
        demo_docs = [
            {
                "name": "Machine Learning Fundamentals",
                "tags": [
                    {"name": "technology", "type": "domain", "confidence": 0.9},
                    {"name": "artificial intelligence", "type": "topic", "confidence": 0.8},
                    {"name": "algorithms", "type": "topic", "confidence": 0.7}
                ]
            },
            {
                "name": "Deep Learning Research Paper",
                "tags": [
                    {"name": "science", "type": "domain", "confidence": 0.8},
                    {"name": "research", "type": "topic", "confidence": 0.9},
                    {"name": "neural networks", "type": "topic", "confidence": 0.8}
                ]
            },
            {
                "name": "Business Analytics Guide",
                "tags": [
                    {"name": "business", "type": "domain", "confidence": 0.9},
                    {"name": "analytics", "type": "topic", "confidence": 0.8},
                    {"name": "strategy", "type": "topic", "confidence": 0.6}
                ]
            },
            {
                "name": "Python Programming Tutorial",
                "tags": [
                    {"name": "technology", "type": "domain", "confidence": 0.9},
                    {"name": "programming", "type": "topic", "confidence": 0.9},
                    {"name": "tutorial", "type": "category", "confidence": 0.8}
                ]
            }
        ]
        
        for doc_data in demo_docs:
            # Check if document already exists
            existing_doc = self.db.query(Document).filter(
                Document.name == doc_data["name"]
            ).first()
            
            if not existing_doc:
                # Create document
                document = Document(
                    name=doc_data["name"],
                    user_id=self.demo_user_id,
                    size=1000,
                    status="processed"
                )
                self.db.add(document)
                self.db.commit()
                self.db.refresh(document)
                
                # Create tags
                for tag_data in doc_data["tags"]:
                    tag = DocumentTag(
                        document_id=document.id,
                        tag_name=tag_data["name"],
                        tag_type=tag_data["type"],
                        confidence_score=tag_data["confidence"],
                        generated_by="demo_system"
                    )
                    self.db.add(tag)
                
                self.db.commit()
    
    async def _create_demo_interactions(self):
        """Create demo user interactions."""
        # Simulate query history
        demo_queries = [
            {
                "query": "machine learning algorithms",
                "satisfaction": 4.5,
                "domains": ["technology", "artificial intelligence"]
            },
            {
                "query": "deep learning neural networks",
                "satisfaction": 4.8,
                "domains": ["science", "technology"]
            },
            {
                "query": "python programming examples",
                "satisfaction": 4.2,
                "domains": ["technology", "programming"]
            },
            {
                "query": "business strategy analysis",
                "satisfaction": 2.5,
                "domains": ["business", "analytics"]
            },
            {
                "query": "research methodology",
                "satisfaction": 3.8,
                "domains": ["science", "research"]
            }
        ]
        
        for query_data in demo_queries:
            # Track query interaction
            await self.profile_manager.track_user_interaction(
                user_id=self.demo_user_id,
                interaction_type="query",
                interaction_data={
                    "query": query_data["query"],
                    "response_time": 1.5,
                    "sources_used": 3,
                    "satisfaction": query_data["satisfaction"]
                }
            )
            
            # Create analytics event
            analytics_event = AnalyticsEvent(
                user_id=self.demo_user_id,
                event_type="query_interaction",
                event_data={
                    "query": query_data["query"],
                    "satisfaction": query_data["satisfaction"],
                    "domains": query_data["domains"]
                }
            )
            self.db.add(analytics_event)
        
        self.db.commit()
    
    async def demo_basic_personalized_search(self):
        """Demonstrate basic personalized search functionality."""
        logger.info("\n=== Demo: Basic Personalized Search ===")
        
        test_queries = [
            "machine learning algorithms",
            "deep learning implementation",
            "business analytics methods",
            "python programming tutorial"
        ]
        
        for query in test_queries:
            logger.info(f"\nQuery: '{query}'")
            
            # Perform personalized search
            results = await self.adaptive_retriever.personalized_search(
                query=query,
                user_id=self.demo_user_id,
                limit=3,
                personalization_level=1.0
            )
            
            logger.info(f"Found {len(results)} personalized results:")
            
            for i, result in enumerate(results, 1):
                metadata = result.get("metadata", {})
                doc_name = metadata.get("document_name", "Unknown")
                base_relevance = result.get("relevance", 0)
                personalized_score = result.get("personalized_score", base_relevance)
                
                logger.info(f"  {i}. {doc_name}")
                logger.info(f"     Base relevance: {base_relevance:.3f}")
                logger.info(f"     Personalized score: {personalized_score:.3f}")
                
                # Show personalization factors if available
                factors = result.get("personalization_factors", {})
                if factors:
                    logger.info(f"     Personalization factors:")
                    for factor, value in factors.items():
                        if value != 0:
                            logger.info(f"       - {factor}: {value:.3f}")
    
    async def demo_personalization_comparison(self):
        """Demonstrate comparison between personalized and non-personalized search."""
        logger.info("\n=== Demo: Personalization Comparison ===")
        
        query = "machine learning algorithms"
        logger.info(f"Query: '{query}'")
        
        # Non-personalized search
        logger.info("\nNon-personalized results:")
        basic_results = await self.adaptive_retriever.personalized_search(
            query=query,
            user_id=self.demo_user_id,
            limit=3,
            personalization_level=0.0
        )
        
        for i, result in enumerate(basic_results, 1):
            doc_name = result.get("metadata", {}).get("document_name", "Unknown")
            relevance = result.get("relevance", 0)
            logger.info(f"  {i}. {doc_name} (relevance: {relevance:.3f})")
        
        # Personalized search
        logger.info("\nPersonalized results:")
        personalized_results = await self.adaptive_retriever.personalized_search(
            query=query,
            user_id=self.demo_user_id,
            limit=3,
            personalization_level=1.0
        )
        
        for i, result in enumerate(personalized_results, 1):
            doc_name = result.get("metadata", {}).get("document_name", "Unknown")
            base_relevance = result.get("relevance", 0)
            personalized_score = result.get("personalized_score", base_relevance)
            logger.info(f"  {i}. {doc_name} (base: {base_relevance:.3f}, personalized: {personalized_score:.3f})")
    
    async def demo_personalization_weights(self):
        """Demonstrate personalization weights calculation."""
        logger.info("\n=== Demo: Personalization Weights ===")
        
        # Get user profile
        user_profile = await self.profile_manager.get_user_profile(self.demo_user_id)
        if user_profile:
            logger.info("User Profile:")
            logger.info(f"  Domain expertise: {user_profile.domain_expertise}")
            logger.info(f"  Learning style: {user_profile.learning_style}")
            logger.info(f"  Total queries: {user_profile.interaction_history.get('total_queries', 0)}")
        
        # Get personalization weights
        weights = await self.adaptive_retriever._get_personalization_weights(
            self.demo_user_id, "machine learning algorithms", user_profile
        )
        
        logger.info("\nPersonalization Weights:")
        for weight_type, value in weights.items():
            if isinstance(value, dict) and value:
                logger.info(f"  {weight_type}:")
                for key, val in value.items():
                    logger.info(f"    - {key}: {val:.3f}")
            elif not isinstance(value, dict):
                logger.info(f"  {weight_type}: {value:.3f}")
    
    async def demo_query_context_analysis(self):
        """Demonstrate query context analysis."""
        logger.info("\n=== Demo: Query Context Analysis ===")
        
        test_queries = [
            "What is machine learning?",
            "How to implement neural networks?",
            "Why does overfitting occur?",
            "Compare CNN and RNN architectures",
            "Advanced deep learning techniques"
        ]
        
        for query in test_queries:
            context = await self.adaptive_retriever._analyze_query_context(query, self.demo_user_id)
            
            logger.info(f"\nQuery: '{query}'")
            logger.info(f"  Question type: {context.get('question_type', 'unknown')}")
            logger.info(f"  Complexity signal: {context.get('complexity_signal', 0):.3f}")
            
            domain_signals = context.get('domain_signals', {})
            if domain_signals:
                logger.info("  Domain signals:")
                for domain, score in domain_signals.items():
                    logger.info(f"    - {domain}: {score:.3f}")
            
            content_signals = context.get('content_type_signals', {})
            if content_signals:
                logger.info("  Content type signals:")
                for content_type, score in content_signals.items():
                    logger.info(f"    - {content_type}: {score:.3f}")
    
    async def demo_retrieval_optimization(self):
        """Demonstrate retrieval optimization based on feedback."""
        logger.info("\n=== Demo: Retrieval Optimization ===")
        
        # Create sample feedback data
        feedback_data = [
            {
                "rating": 5,
                "domains": ["technology", "artificial intelligence"],
                "query": "machine learning algorithms",
                "timestamp": datetime.utcnow().isoformat()
            },
            {
                "rating": 5,
                "domains": ["technology", "programming"],
                "query": "python programming examples",
                "timestamp": datetime.utcnow().isoformat()
            },
            {
                "rating": 2,
                "domains": ["business", "analytics"],
                "query": "business strategy analysis",
                "timestamp": datetime.utcnow().isoformat()
            },
            {
                "rating": 4,
                "domains": ["science", "research"],
                "query": "research methodology",
                "timestamp": datetime.utcnow().isoformat()
            }
        ]
        
        logger.info("Sample feedback data:")
        for feedback in feedback_data:
            logger.info(f"  Query: '{feedback['query']}' - Rating: {feedback['rating']}/5")
        
        # Analyze feedback patterns
        analysis = self.retrieval_optimizer._analyze_feedback_patterns(feedback_data)
        logger.info(f"\nFeedback Analysis:")
        logger.info(f"  Average rating: {analysis['avg_rating']:.2f}")
        logger.info(f"  Total feedback items: {analysis['total_feedback']}")
        logger.info(f"  Satisfaction trend: {analysis['satisfaction_trend']}")
        
        if analysis['preferred_domains']:
            logger.info("  Preferred domains:")
            for domain, count in analysis['preferred_domains']:
                logger.info(f"    - {domain}: {count} positive mentions")
        
        if analysis['avoided_domains']:
            logger.info("  Avoided domains:")
            for domain, count in analysis['avoided_domains']:
                logger.info(f"    - {domain}: {count} negative mentions")
        
        # Generate optimization recommendations
        user_profile = await self.profile_manager.get_user_profile(self.demo_user_id)
        recommendations = await self.retrieval_optimizer._generate_optimization_recommendations(
            analysis, user_profile
        )
        
        logger.info(f"\nOptimization Recommendations (confidence: {recommendations['confidence']:.2f}):")
        
        domain_adjustments = recommendations.get('domain_weight_adjustments', {})
        if domain_adjustments:
            logger.info("  Domain weight adjustments:")
            for domain, adjustment in domain_adjustments.items():
                direction = "increase" if adjustment > 0 else "decrease"
                logger.info(f"    - {domain}: {direction} by {abs(adjustment):.2f}")
        
        personalization_adj = recommendations.get('personalization_level_adjustment', 0)
        if personalization_adj != 0:
            direction = "increase" if personalization_adj > 0 else "decrease"
            logger.info(f"  Personalization level: {direction} by {abs(personalization_adj):.2f}")
        
        # Apply optimizations if confidence is high enough
        if recommendations['confidence'] > 0.7:
            logger.info("\nApplying optimizations (high confidence)...")
            optimization_result = await self.retrieval_optimizer.optimize_for_user(
                self.demo_user_id, feedback_data
            )
            logger.info(f"Optimization result: {optimization_result}")
        else:
            logger.info("\nSkipping automatic optimization (low confidence)")
    
    async def demo_personalization_stats(self):
        """Demonstrate personalization statistics."""
        logger.info("\n=== Demo: Personalization Statistics ===")
        
        # Get personalization stats
        stats = await self.adaptive_retriever.get_personalization_stats(self.demo_user_id)
        
        logger.info("Personalization Statistics:")
        for key, value in stats.items():
            if isinstance(value, dict):
                logger.info(f"  {key}:")
                for sub_key, sub_value in value.items():
                    logger.info(f"    - {sub_key}: {sub_value}")
            else:
                logger.info(f"  {key}: {value}")
    
    async def run_all_demos(self):
        """Run all demo scenarios."""
        try:
            await self.setup_demo_data()
            
            await self.demo_basic_personalized_search()
            await self.demo_personalization_comparison()
            await self.demo_personalization_weights()
            await self.demo_query_context_analysis()
            await self.demo_retrieval_optimization()
            await self.demo_personalization_stats()
            
            logger.info("\n=== All demos completed successfully! ===")
            
        except Exception as e:
            logger.error(f"Demo error: {str(e)}")
            raise
        finally:
            self.db.close()

async def main():
    """Main demo function."""
    logger.info("Starting Adaptive Retrieval System Demo")
    
    demo = AdaptiveRetrievalDemo()
    await demo.run_all_demos()

if __name__ == "__main__":
    asyncio.run(main())