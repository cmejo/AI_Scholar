"""
Domain Adaptation Demo

This script demonstrates the domain adaptation capabilities including:
- Domain detection from user interactions
- Domain-specific retrieval strategies
- Document domain classification
- Adaptive learning from feedback
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from core.database import get_db, UserProfile, DocumentTag, AnalyticsEvent, Message, Document
from services.domain_adapter import DomainAdapter, DomainDetector
from services.user_profile_service import UserProfileManager
from models.schemas import UserPreferences

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DomainAdaptationDemo:
    """Demo class for domain adaptation features."""
    
    def __init__(self):
        self.db = next(get_db())
        self.domain_adapter = DomainAdapter(self.db)
        self.domain_detector = DomainDetector(self.db)
        self.profile_manager = UserProfileManager(self.db)
    
    async def run_demo(self):
        """Run the complete domain adaptation demo."""
        print("🔧 Domain Adaptation System Demo")
        print("=" * 50)
        
        try:
            # Setup demo data
            await self.setup_demo_data()
            
            # Demo 1: Domain Detection
            await self.demo_domain_detection()
            
            # Demo 2: Domain-Specific Strategies
            await self.demo_domain_strategies()
            
            # Demo 3: Document Domain Classification
            await self.demo_document_classification()
            
            # Demo 4: Retrieval Adaptation
            await self.demo_retrieval_adaptation()
            
            # Demo 5: Learning and Feedback
            await self.demo_learning_feedback()
            
            # Demo 6: Analytics and Stats
            await self.demo_analytics()
            
            print("\n✅ Domain Adaptation Demo completed successfully!")
            
        except Exception as e:
            logger.error(f"Demo failed: {str(e)}")
            print(f"\n❌ Demo failed: {str(e)}")
        finally:
            self.db.close()
    
    async def setup_demo_data(self):
        """Setup demo data for testing."""
        print("\n📊 Setting up demo data...")
        
        # Create test user profile
        test_user_id = "demo-user-1"
        
        # Check if profile exists
        existing_profile = self.db.query(UserProfile).filter(
            UserProfile.user_id == test_user_id
        ).first()
        
        if not existing_profile:
            preferences = UserPreferences(
                language="en",
                response_style="detailed",
                domain_focus=["technology", "science"],
                citation_preference="inline"
            )
            
            await self.profile_manager.create_user_profile(
                user_id=test_user_id,
                preferences=preferences,
                learning_style="visual"
            )
        
        # Create sample analytics events
        sample_events = [
            {
                "event_type": "adaptive_search",
                "event_data": {
                    "query": "machine learning algorithms",
                    "top_domains": ["technology", "science"],
                    "results_count": 5
                }
            },
            {
                "event_type": "chat_interaction",
                "event_data": {
                    "query": "software architecture patterns",
                    "response_time": 1.2
                }
            },
            {
                "event_type": "adaptive_search",
                "event_data": {
                    "query": "clinical trial methodology",
                    "top_domains": ["medicine", "science"],
                    "results_count": 3
                }
            }
        ]
        
        for event_data in sample_events:
            event = AnalyticsEvent(
                user_id=test_user_id,
                event_type=event_data["event_type"],
                event_data=event_data["event_data"],
                timestamp=datetime.utcnow() - timedelta(days=1)
            )
            self.db.add(event)
        
        # Create sample messages
        sample_messages = [
            "How do machine learning algorithms work?",
            "Explain software development best practices",
            "What is the research methodology for clinical studies?",
            "How to implement API authentication?",
            "Describe the scientific method in research"
        ]
        
        for i, content in enumerate(sample_messages):
            message = Message(
                id=f"msg-{i+1}",
                conversation_id=f"conv-1",
                user_id=test_user_id,
                role="user",
                content=content,
                created_at=datetime.utcnow() - timedelta(hours=i)
            )
            self.db.add(message)
        
        # Create sample document tags
        sample_tags = [
            {"document_id": "doc-1", "tag_name": "technology", "confidence": 0.9},
            {"document_id": "doc-1", "tag_name": "programming", "confidence": 0.8},
            {"document_id": "doc-2", "tag_name": "science", "confidence": 0.85},
            {"document_id": "doc-2", "tag_name": "research", "confidence": 0.7},
            {"document_id": "doc-3", "tag_name": "medicine", "confidence": 0.9},
            {"document_id": "doc-3", "tag_name": "clinical", "confidence": 0.8}
        ]
        
        for tag_data in sample_tags:
            tag = DocumentTag(
                document_id=tag_data["document_id"],
                tag_name=tag_data["tag_name"],
                tag_type="domain",
                confidence_score=tag_data["confidence"],
                generated_by="demo_setup"
            )
            self.db.add(tag)
        
        self.db.commit()
        print("✅ Demo data setup complete")
    
    async def demo_domain_detection(self):
        """Demonstrate domain detection capabilities."""
        print("\n🎯 Demo 1: Domain Detection")
        print("-" * 30)
        
        test_user_id = "demo-user-1"
        
        # Detect user domains
        detected_domains = await self.domain_adapter.detect_user_domains(test_user_id)
        
        print(f"Detected domains for user {test_user_id}:")
        for domain, confidence in sorted(detected_domains.items(), key=lambda x: x[1], reverse=True):
            print(f"  • {domain}: {confidence:.3f}")
        
        # Test query domain detection
        test_queries = [
            "How to implement machine learning algorithms?",
            "What is the clinical trial methodology?",
            "Explain business strategy and market analysis",
            "Legal compliance and regulatory requirements"
        ]
        
        print("\nQuery domain detection:")
        for query in test_queries:
            query_domains = self.domain_adapter._detect_query_domains(query)
            top_domain = max(query_domains.items(), key=lambda x: x[1]) if query_domains else ("none", 0)
            print(f"  Query: '{query[:50]}...'")
            print(f"  Top domain: {top_domain[0]} ({top_domain[1]:.3f})")
    
    async def demo_domain_strategies(self):
        """Demonstrate domain-specific strategies."""
        print("\n⚙️ Demo 2: Domain-Specific Strategies")
        print("-" * 40)
        
        test_user_id = "demo-user-1"
        
        # Test different domain strategies
        test_scenarios = [
            ("technology", "How to implement REST API authentication?"),
            ("medicine", "What is the treatment protocol for diabetes?"),
            ("science", "Explain the research methodology for this study"),
            ("business", "What is the market strategy for growth?"),
            ("law", "What are the compliance requirements?")
        ]
        
        for expected_domain, query in test_scenarios:
            print(f"\nScenario: {expected_domain.title()} Query")
            print(f"Query: '{query}'")
            
            strategy = await self.domain_adapter.get_domain_specific_strategy(
                test_user_id, query
            )
            
            print(f"Primary domain: {strategy['primary_domain']}")
            print(f"Domain confidence: {strategy['domain_confidence']:.3f}")
            print(f"Chunk size: {strategy['chunking_strategy']['chunk_size']}")
            print(f"Overlap ratio: {strategy['chunking_strategy']['overlap_ratio']}")
            print(f"Citation style: {strategy['response_strategy']['citation_style']}")
            print(f"Detail level: {strategy['response_strategy']['detail_level']}")
    
    async def demo_document_classification(self):
        """Demonstrate document domain classification."""
        print("\n📄 Demo 3: Document Domain Classification")
        print("-" * 45)
        
        # Test document samples
        test_documents = [
            {
                "id": "tech-doc",
                "content": """
                This guide covers software development best practices, including
                API design, database optimization, and machine learning implementation.
                Topics include programming languages, algorithms, and framework usage.
                """
            },
            {
                "id": "medical-doc",
                "content": """
                Clinical guidelines for patient treatment and diagnosis procedures.
                This medical protocol covers therapeutic interventions, healthcare
                delivery, and clinical research methodologies for patient care.
                """
            },
            {
                "id": "business-doc",
                "content": """
                Market analysis report covering business strategy, revenue optimization,
                and financial performance metrics. Includes management recommendations
                for corporate growth and profit maximization strategies.
                """
            },
            {
                "id": "science-doc",
                "content": """
                Research paper presenting experimental methodology and scientific analysis.
                The study includes hypothesis testing, theoretical framework, and
                empirical research findings with statistical significance.
                """
            }
        ]
        
        for doc in test_documents:
            print(f"\nDocument: {doc['id']}")
            print(f"Content preview: {doc['content'][:100]}...")
            
            detected_domains = await self.domain_detector.detect_document_domain(
                doc['id'], doc['content']
            )
            
            print("Detected domains:")
            for domain, confidence in detected_domains:
                print(f"  • {domain}: {confidence:.3f}")
    
    async def demo_retrieval_adaptation(self):
        """Demonstrate retrieval result adaptation."""
        print("\n🔍 Demo 4: Retrieval Adaptation")
        print("-" * 35)
        
        # Mock retrieval results
        mock_results = [
            {
                "content": "Machine learning algorithms and software development practices",
                "relevance": 0.8,
                "metadata": {
                    "document_id": "doc-1",
                    "document_name": "Tech Guide",
                    "content_length": 1200
                }
            },
            {
                "content": "Clinical research methodology and medical treatment protocols",
                "relevance": 0.75,
                "metadata": {
                    "document_id": "doc-3",
                    "document_name": "Medical Guidelines",
                    "content_length": 1500
                }
            },
            {
                "content": "Business strategy and market analysis framework",
                "relevance": 0.7,
                "metadata": {
                    "document_id": "doc-4",
                    "document_name": "Business Report",
                    "content_length": 800
                }
            }
        ]
        
        # Test with technology strategy
        tech_strategy = {
            "primary_domain": "technology",
            "domain_confidence": 0.8,
            "all_domains": {"technology": 0.8, "science": 0.3},
            "retrieval_strategy": {
                "domain_boost": 0.24,
                "content_type_preference": ["documentation", "tutorial"],
                "complexity_weight": 0.8,
                "recency_weight": 0.9
            }
        }
        
        print("Original results (by relevance):")
        for i, result in enumerate(mock_results, 1):
            print(f"  {i}. {result['metadata']['document_name']}: {result['relevance']:.3f}")
        
        # Adapt results
        adapted_results = await self.domain_adapter.adapt_retrieval_results(
            mock_results, tech_strategy, "demo-user-1"
        )
        
        print("\nAdapted results (technology domain):")
        for i, result in enumerate(adapted_results, 1):
            score = result.get("domain_adapted_score", result["relevance"])
            factors = result.get("domain_factors", {})
            print(f"  {i}. {result['metadata']['document_name']}: {score:.3f}")
            if factors:
                print(f"     Domain score: {factors.get('domain_score', 0):.3f}")
                print(f"     Content type: {factors.get('content_type_score', 0):.3f}")
    
    async def demo_learning_feedback(self):
        """Demonstrate learning and feedback mechanisms."""
        print("\n🧠 Demo 5: Learning and Feedback")
        print("-" * 35)
        
        test_user_id = "demo-user-1"
        
        # Simulate user interaction with feedback
        query = "How to implement secure API authentication?"
        results = [
            {"metadata": {"document_id": "doc-1"}},
            {"metadata": {"document_id": "doc-2"}}
        ]
        
        # Positive feedback
        positive_feedback = {
            "rating": 5,
            "helpful": True,
            "comment": "Very relevant and detailed"
        }
        
        print(f"Query: '{query}'")
        print(f"User feedback: {positive_feedback}")
        
        # Update domain adaptation
        await self.domain_adapter.update_domain_adaptation(
            test_user_id, query, results, positive_feedback
        )
        
        print("✅ Domain adaptation updated with positive feedback")
        
        # Show learning effect
        updated_domains = await self.domain_adapter.detect_user_domains(test_user_id)
        print("\nUpdated domain expertise:")
        for domain, confidence in sorted(updated_domains.items(), key=lambda x: x[1], reverse=True):
            print(f"  • {domain}: {confidence:.3f}")
    
    async def demo_analytics(self):
        """Demonstrate analytics and statistics."""
        print("\n📊 Demo 6: Analytics and Statistics")
        print("-" * 40)
        
        test_user_id = "demo-user-1"
        
        # Get domain adaptation stats
        stats = await self.domain_adapter.get_domain_adaptation_stats(test_user_id)
        
        print("Domain Adaptation Statistics:")
        print(f"  Primary domain: {stats.get('primary_domain', 'None')}")
        print(f"  Domain confidence: {stats.get('domain_confidence', 0):.3f}")
        print(f"  Adaptation events: {stats.get('adaptation_events', 0)}")
        print(f"  Learning trend: {stats.get('learning_trend', 'unknown')}")
        
        detected_domains = stats.get('detected_domains', {})
        if detected_domains:
            print("\n  Detected domains:")
            for domain, confidence in sorted(detected_domains.items(), key=lambda x: x[1], reverse=True):
                print(f"    • {domain}: {confidence:.3f}")
        
        domain_distribution = stats.get('domain_distribution', {})
        if domain_distribution:
            print("\n  Domain query distribution:")
            for domain, count in domain_distribution.items():
                print(f"    • {domain}: {count} queries")
    
    def print_domain_configs(self):
        """Print domain configuration details."""
        print("\n🔧 Domain Configurations")
        print("-" * 25)
        
        for domain, config in DomainAdapter.DOMAIN_CONFIGS.items():
            print(f"\n{domain.title()} Domain:")
            print(f"  Chunk size: {config['chunk_size']}")
            print(f"  Overlap ratio: {config['overlap_ratio']}")
            print(f"  Complexity weight: {config['complexity_weight']}")
            print(f"  Recency weight: {config['recency_weight']}")
            print(f"  Citation style: {config['citation_style']}")
            print(f"  Content types: {', '.join(config['content_types'])}")
            print(f"  Keywords: {', '.join(config['keywords'][:5])}...")

async def main():
    """Run the domain adaptation demo."""
    demo = DomainAdaptationDemo()
    await demo.run_demo()
    
    # Print configuration details
    demo.print_domain_configs()

if __name__ == "__main__":
    asyncio.run(main())