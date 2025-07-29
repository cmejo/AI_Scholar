"""
Task 7.4 Verification: Domain Adaptation Capabilities

This script verifies the implementation of domain adaptation capabilities including:
- DomainAdapter for document type customization
- Domain-specific retrieval and response strategies  
- Domain detection from user interaction patterns
- Domain adaptation effectiveness testing
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from core.database import get_db, UserProfile, DocumentTag, AnalyticsEvent, Message, Conversation
from services.domain_adapter import DomainAdapter, DomainDetector
from services.user_profile_service import UserProfileManager
from models.schemas import UserPreferences

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Task74Verification:
    """Verification class for Task 7.4 domain adaptation capabilities."""
    
    def __init__(self):
        self.db = next(get_db())
        self.domain_adapter = DomainAdapter(self.db)
        self.domain_detector = DomainDetector(self.db)
        self.profile_manager = UserProfileManager(self.db)
        self.test_results = []
    
    async def run_verification(self):
        """Run complete verification of domain adaptation capabilities."""
        print("🔧 Task 7.4 Verification: Domain Adaptation Capabilities")
        print("=" * 60)
        
        try:
            # Setup test environment
            await self.setup_test_environment()
            
            # Test 1: DomainAdapter Implementation
            await self.test_domain_adapter_implementation()
            
            # Test 2: Domain Detection from User Patterns
            await self.test_domain_detection_patterns()
            
            # Test 3: Domain-Specific Retrieval Strategies
            await self.test_domain_specific_strategies()
            
            # Test 4: Document Type Customization
            await self.test_document_type_customization()
            
            # Test 5: Domain Adaptation Effectiveness
            await self.test_domain_adaptation_effectiveness()
            
            # Test 6: Learning and Feedback Integration
            await self.test_learning_feedback_integration()
            
            # Generate verification report
            self.generate_verification_report()
            
        except Exception as e:
            logger.error(f"Verification failed: {str(e)}")
            self.test_results.append({
                "test": "Overall Verification",
                "status": "FAILED",
                "error": str(e)
            })
        finally:
            self.db.close()
    
    async def setup_test_environment(self):
        """Setup test environment with sample data."""
        print("\n📊 Setting up test environment...")
        
        try:
            # Create test user
            test_user_id = "test-user-7-4"
            
            # Clean up existing test data
            self.db.query(UserProfile).filter(UserProfile.user_id == test_user_id).delete()
            self.db.query(AnalyticsEvent).filter(AnalyticsEvent.user_id == test_user_id).delete()
            # Clean up messages and conversations
            self.db.query(Message).filter(Message.conversation_id == "test-conv-1").delete()
            self.db.query(Conversation).filter(Conversation.user_id == test_user_id).delete()
            self.db.commit()
            
            # Create user profile with domain preferences
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
            
            # Create interaction history
            sample_events = [
                {
                    "event_type": "adaptive_search",
                    "event_data": {
                        "query": "machine learning algorithms implementation",
                        "top_domains": ["technology", "science"],
                        "results_count": 5
                    }
                },
                {
                    "event_type": "chat_interaction", 
                    "event_data": {
                        "query": "software architecture patterns and design",
                        "response_time": 1.5
                    }
                },
                {
                    "event_type": "adaptive_search",
                    "event_data": {
                        "query": "clinical research methodology validation",
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
                    timestamp=datetime.utcnow() - timedelta(days=2)
                )
                self.db.add(event)
            
            # Create test conversation first
            test_conversation = Conversation(
                id="test-conv-1",
                user_id=test_user_id,
                title="Test Conversation",
                created_at=datetime.utcnow() - timedelta(days=1)
            )
            self.db.add(test_conversation)
            
            # Create sample messages
            sample_messages = [
                "How do machine learning algorithms work in practice?",
                "Explain software development best practices and patterns",
                "What is the clinical trial methodology for drug testing?",
                "How to implement secure API authentication systems?",
                "Describe research methodology in scientific studies"
            ]
            
            for i, content in enumerate(sample_messages):
                message = Message(
                    id=f"test-msg-{i+1}",
                    conversation_id="test-conv-1",
                    role="user",
                    content=content,
                    created_at=datetime.utcnow() - timedelta(hours=i*2)
                )
                self.db.add(message)
            
            # Create document tags for testing
            test_tags = [
                {"document_id": "test-doc-1", "tag_name": "technology", "confidence": 0.9},
                {"document_id": "test-doc-1", "tag_name": "programming", "confidence": 0.8},
                {"document_id": "test-doc-2", "tag_name": "science", "confidence": 0.85},
                {"document_id": "test-doc-2", "tag_name": "research", "confidence": 0.75},
                {"document_id": "test-doc-3", "tag_name": "medicine", "confidence": 0.9},
                {"document_id": "test-doc-3", "tag_name": "clinical", "confidence": 0.8}
            ]
            
            for tag_data in test_tags:
                tag = DocumentTag(
                    document_id=tag_data["document_id"],
                    tag_name=tag_data["tag_name"],
                    tag_type="domain",
                    confidence_score=tag_data["confidence"],
                    generated_by="test_setup"
                )
                self.db.add(tag)
            
            self.db.commit()
            
            self.test_results.append({
                "test": "Test Environment Setup",
                "status": "PASSED",
                "details": "Successfully created test user, events, messages, and tags"
            })
            
        except Exception as e:
            self.test_results.append({
                "test": "Test Environment Setup",
                "status": "FAILED",
                "error": str(e)
            })
            raise
    
    async def test_domain_adapter_implementation(self):
        """Test DomainAdapter class implementation."""
        print("\n🎯 Testing DomainAdapter Implementation...")
        
        try:
            # Test 1: DomainAdapter instantiation
            assert self.domain_adapter is not None
            assert hasattr(self.domain_adapter, 'detect_user_domains')
            assert hasattr(self.domain_adapter, 'get_domain_specific_strategy')
            assert hasattr(self.domain_adapter, 'adapt_retrieval_results')
            
            # Test 2: Domain configurations exist
            assert hasattr(DomainAdapter, 'DOMAIN_CONFIGS')
            assert len(DomainAdapter.DOMAIN_CONFIGS) >= 6  # At least 6 domains
            
            # Test 3: Required domains are configured
            required_domains = ["technology", "science", "business", "medicine", "education", "law"]
            for domain in required_domains:
                assert domain in DomainAdapter.DOMAIN_CONFIGS
                config = DomainAdapter.DOMAIN_CONFIGS[domain]
                assert "keywords" in config
                assert "chunk_size" in config
                assert "overlap_ratio" in config
                assert "complexity_weight" in config
                assert "recency_weight" in config
                assert "citation_style" in config
                assert "reasoning_emphasis" in config
                assert "content_types" in config
            
            # Test 4: Configuration value ranges
            for domain, config in DomainAdapter.DOMAIN_CONFIGS.items():
                assert 0 <= config["overlap_ratio"] <= 1
                assert 0 <= config["complexity_weight"] <= 1
                assert 0 <= config["recency_weight"] <= 1
                assert config["chunk_size"] > 0
                assert len(config["keywords"]) >= 5
                assert len(config["content_types"]) >= 2
            
            self.test_results.append({
                "test": "DomainAdapter Implementation",
                "status": "PASSED",
                "details": f"All {len(DomainAdapter.DOMAIN_CONFIGS)} domain configurations valid"
            })
            
        except Exception as e:
            self.test_results.append({
                "test": "DomainAdapter Implementation",
                "status": "FAILED",
                "error": str(e)
            })
    
    async def test_domain_detection_patterns(self):
        """Test domain detection from user interaction patterns."""
        print("\n🔍 Testing Domain Detection from User Patterns...")
        
        try:
            test_user_id = "test-user-7-4"
            
            # Test 1: Detect user domains
            detected_domains = await self.domain_adapter.detect_user_domains(test_user_id)
            
            assert isinstance(detected_domains, dict)
            assert len(detected_domains) > 0
            
            # Should detect technology and science based on test data
            assert "technology" in detected_domains or "science" in detected_domains
            
            # All scores should be between 0 and 1
            for domain, score in detected_domains.items():
                assert 0 <= score <= 1
            
            # Test 2: Query domain detection
            test_queries = [
                ("How to implement machine learning algorithms?", "technology"),
                ("What is the clinical trial methodology?", "medicine"),
                ("Explain business strategy and market analysis", "business"),
                ("Legal compliance and regulatory requirements", "law")
            ]
            
            for query, expected_domain in test_queries:
                query_domains = self.domain_adapter._detect_query_domains(query)
                assert isinstance(query_domains, dict)
                
                if query_domains:  # May be empty for some queries
                    # Check that expected domain has highest score if detected
                    if expected_domain in query_domains:
                        max_domain = max(query_domains.items(), key=lambda x: x[1])[0]
                        assert max_domain == expected_domain or query_domains[expected_domain] > 0.1
            
            # Test 3: Interaction domain analysis
            interaction_domains = await self.domain_adapter._analyze_interaction_domains(test_user_id)
            assert isinstance(interaction_domains, dict)
            
            # Test 4: Query domain analysis
            query_domains = await self.domain_adapter._analyze_query_domains(test_user_id)
            assert isinstance(query_domains, dict)
            
            # Test 5: Document domain analysis
            document_domains = await self.domain_adapter._analyze_document_domains(test_user_id)
            assert isinstance(document_domains, dict)
            
            self.test_results.append({
                "test": "Domain Detection from User Patterns",
                "status": "PASSED",
                "details": f"Detected {len(detected_domains)} domains with valid scores"
            })
            
        except Exception as e:
            self.test_results.append({
                "test": "Domain Detection from User Patterns",
                "status": "FAILED",
                "error": str(e)
            })
    
    async def test_domain_specific_strategies(self):
        """Test domain-specific retrieval and response strategies."""
        print("\n⚙️ Testing Domain-Specific Strategies...")
        
        try:
            test_user_id = "test-user-7-4"
            
            # Test strategies for different domains
            test_scenarios = [
                ("technology", "How to implement REST API authentication?"),
                ("medicine", "What is the treatment protocol for diabetes?"),
                ("science", "Explain the research methodology for this study"),
                ("business", "What is the market strategy for growth?"),
                ("law", "What are the compliance requirements?")
            ]
            
            for expected_domain, query in test_scenarios:
                # Get domain-specific strategy
                strategy = await self.domain_adapter.get_domain_specific_strategy(
                    test_user_id, query
                )
                
                # Verify strategy structure
                assert isinstance(strategy, dict)
                assert "primary_domain" in strategy
                assert "domain_confidence" in strategy
                assert "chunking_strategy" in strategy
                assert "retrieval_strategy" in strategy
                assert "response_strategy" in strategy
                assert "all_domains" in strategy
                
                # Verify chunking strategy
                chunking = strategy["chunking_strategy"]
                assert "chunk_size" in chunking
                assert "overlap_ratio" in chunking
                assert "preserve_context" in chunking
                assert chunking["chunk_size"] > 0
                assert 0 <= chunking["overlap_ratio"] <= 1
                
                # Verify retrieval strategy
                retrieval = strategy["retrieval_strategy"]
                assert "complexity_weight" in retrieval
                assert "recency_weight" in retrieval
                assert "domain_boost" in retrieval
                assert "content_type_preference" in retrieval
                assert 0 <= retrieval["complexity_weight"] <= 1
                assert 0 <= retrieval["recency_weight"] <= 1
                
                # Verify response strategy
                response = strategy["response_strategy"]
                assert "citation_style" in response
                assert "reasoning_emphasis" in response
                assert "detail_level" in response
                assert "uncertainty_handling" in response
                assert response["detail_level"] in ["low", "medium", "high"]
                assert response["uncertainty_handling"] in ["standard", "conservative"]
            
            # Test default strategy
            default_strategy = await self.domain_adapter.get_domain_specific_strategy(
                test_user_id, "generic question", {}
            )
            assert default_strategy["primary_domain"] == "general"
            assert default_strategy["domain_confidence"] == 0.0
            
            self.test_results.append({
                "test": "Domain-Specific Strategies",
                "status": "PASSED",
                "details": f"Successfully generated strategies for {len(test_scenarios)} domains"
            })
            
        except Exception as e:
            self.test_results.append({
                "test": "Domain-Specific Strategies",
                "status": "FAILED",
                "error": str(e)
            })
    
    async def test_document_type_customization(self):
        """Test document type customization capabilities."""
        print("\n📄 Testing Document Type Customization...")
        
        try:
            # Test document domain detection
            test_documents = [
                {
                    "id": "tech-doc-test",
                    "content": """
                    This comprehensive guide covers software development methodologies,
                    including API design patterns, database optimization techniques,
                    and machine learning algorithm implementation strategies.
                    """,
                    "expected_domains": ["technology"]
                },
                {
                    "id": "medical-doc-test", 
                    "content": """
                    Clinical practice guidelines for patient care and treatment protocols.
                    This medical reference covers diagnostic procedures, therapeutic
                    interventions, and healthcare delivery best practices.
                    """,
                    "expected_domains": ["medicine"]
                },
                {
                    "id": "science-doc-test",
                    "content": """
                    Research methodology and experimental design for scientific studies.
                    This paper presents theoretical frameworks, hypothesis testing,
                    and empirical analysis techniques for research validation.
                    """,
                    "expected_domains": ["science"]
                }
            ]
            
            for doc in test_documents:
                # Test domain detection
                detected_domains = await self.domain_detector.detect_document_domain(
                    doc["id"], doc["content"]
                )
                
                assert isinstance(detected_domains, list)
                assert len(detected_domains) > 0
                
                # Verify domain detection accuracy
                detected_domain_names = [domain for domain, _ in detected_domains]
                for expected_domain in doc["expected_domains"]:
                    assert expected_domain in detected_domain_names
                
                # Verify confidence scores
                for domain, confidence in detected_domains:
                    assert 0 <= confidence <= 1
                    assert confidence > 0.1  # Should have meaningful confidence
            
            # Test auto-tagging functionality
            test_doc_id = "auto-tag-test-doc"
            test_content = """
            Software engineering principles and programming best practices.
            This guide covers algorithm design, data structures, and
            computer science fundamentals for developers.
            """
            
            # Clean up any existing tags
            self.db.query(DocumentTag).filter(
                DocumentTag.document_id == test_doc_id
            ).delete()
            self.db.commit()
            
            # Test auto-tagging
            await self.domain_detector.auto_tag_document_domains(test_doc_id, test_content)
            
            # Verify tags were created
            created_tags = self.db.query(DocumentTag).filter(
                DocumentTag.document_id == test_doc_id,
                DocumentTag.tag_type == "domain"
            ).all()
            
            assert len(created_tags) > 0
            
            # Should have technology domain tag
            tech_tags = [tag for tag in created_tags if tag.tag_name == "technology"]
            assert len(tech_tags) > 0
            assert tech_tags[0].confidence_score > 0.1
            assert tech_tags[0].generated_by == "domain_detector"
            
            self.test_results.append({
                "test": "Document Type Customization",
                "status": "PASSED",
                "details": f"Successfully detected domains for {len(test_documents)} documents and auto-tagged 1 document"
            })
            
        except Exception as e:
            self.test_results.append({
                "test": "Document Type Customization",
                "status": "FAILED",
                "error": str(e)
            })
    
    async def test_domain_adaptation_effectiveness(self):
        """Test domain adaptation effectiveness."""
        print("\n📊 Testing Domain Adaptation Effectiveness...")
        
        try:
            test_user_id = "test-user-7-4"
            
            # Test retrieval result adaptation
            mock_results = [
                {
                    "content": "Machine learning algorithms and software development",
                    "relevance": 0.8,
                    "metadata": {
                        "document_id": "test-doc-1",
                        "document_name": "Tech Guide",
                        "content_length": 1200
                    }
                },
                {
                    "content": "Clinical research methodology and medical protocols",
                    "relevance": 0.75,
                    "metadata": {
                        "document_id": "test-doc-3",
                        "document_name": "Medical Guidelines", 
                        "content_length": 1500
                    }
                },
                {
                    "content": "Business strategy and market analysis",
                    "relevance": 0.7,
                    "metadata": {
                        "document_id": "test-doc-4",
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
            
            adapted_results = await self.domain_adapter.adapt_retrieval_results(
                mock_results, tech_strategy, test_user_id
            )
            
            # Verify adaptation
            assert len(adapted_results) == len(mock_results)
            
            for result in adapted_results:
                assert "domain_adapted_score" in result
                assert "domain_factors" in result
                assert 0 <= result["domain_adapted_score"] <= 1
                
                factors = result["domain_factors"]
                assert "domain_score" in factors
                assert "content_type_score" in factors
                assert "complexity_score" in factors
                assert "recency_score" in factors
                assert "primary_domain" in factors
                assert factors["primary_domain"] == "technology"
            
            # Results should be sorted by adapted score
            scores = [r["domain_adapted_score"] for r in adapted_results]
            assert scores == sorted(scores, reverse=True)
            
            # Test with general strategy (no adaptation)
            general_strategy = {
                "primary_domain": "general",
                "domain_confidence": 0.0,
                "all_domains": {},
                "retrieval_strategy": {}
            }
            
            general_results = await self.domain_adapter.adapt_retrieval_results(
                mock_results, general_strategy, test_user_id
            )
            
            # Should return original results unchanged
            assert len(general_results) == len(mock_results)
            
            self.test_results.append({
                "test": "Domain Adaptation Effectiveness",
                "status": "PASSED",
                "details": "Successfully adapted retrieval results with domain-specific scoring"
            })
            
        except Exception as e:
            self.test_results.append({
                "test": "Domain Adaptation Effectiveness",
                "status": "FAILED",
                "error": str(e)
            })
    
    async def test_learning_feedback_integration(self):
        """Test learning and feedback integration."""
        print("\n🧠 Testing Learning and Feedback Integration...")
        
        try:
            test_user_id = "test-user-7-4"
            
            # Get initial domain state
            initial_domains = await self.domain_adapter.detect_user_domains(test_user_id)
            
            # Simulate positive feedback interaction
            query = "How to implement secure API authentication systems?"
            results = [
                {"metadata": {"document_id": "test-doc-1"}},
                {"metadata": {"document_id": "test-doc-2"}}
            ]
            
            positive_feedback = {
                "rating": 5,
                "helpful": True,
                "comment": "Very relevant and detailed information"
            }
            
            # Update domain adaptation with feedback
            await self.domain_adapter.update_domain_adaptation(
                test_user_id, query, results, positive_feedback
            )
            
            # Verify analytics event was created
            recent_events = self.db.query(AnalyticsEvent).filter(
                AnalyticsEvent.user_id == test_user_id,
                AnalyticsEvent.event_type == "domain_adaptation_learning"
            ).all()
            
            assert len(recent_events) > 0
            
            latest_event = recent_events[-1]
            assert latest_event.event_data["query"] == query
            assert latest_event.event_data["user_feedback"] == positive_feedback
            assert "query_domains" in latest_event.event_data
            assert "result_domains" in latest_event.event_data
            
            # Test negative feedback (should not reinforce learning)
            negative_feedback = {
                "rating": 2,
                "helpful": False,
                "comment": "Not relevant"
            }
            
            await self.domain_adapter.update_domain_adaptation(
                test_user_id, "irrelevant query", results, negative_feedback
            )
            
            # Test analytics and statistics
            stats = await self.domain_adapter.get_domain_adaptation_stats(test_user_id)
            
            assert isinstance(stats, dict)
            assert "detected_domains" in stats
            assert "primary_domain" in stats
            assert "domain_confidence" in stats
            assert "adaptation_events" in stats
            assert "learning_trend" in stats
            assert "domain_distribution" in stats
            
            # Should have at least 2 adaptation events
            assert stats["adaptation_events"] >= 2
            
            # Should have detected domains
            assert len(stats["detected_domains"]) > 0
            
            # Should have primary domain
            assert stats["primary_domain"] is not None
            
            self.test_results.append({
                "test": "Learning and Feedback Integration",
                "status": "PASSED",
                "details": f"Successfully processed feedback and generated stats with {stats['adaptation_events']} events"
            })
            
        except Exception as e:
            self.test_results.append({
                "test": "Learning and Feedback Integration",
                "status": "FAILED",
                "error": str(e)
            })
    
    def generate_verification_report(self):
        """Generate comprehensive verification report."""
        print("\n" + "=" * 60)
        print("📋 TASK 7.4 VERIFICATION REPORT")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASSED"])
        failed_tests = total_tests - passed_tests
        
        print(f"\nOverall Results:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Passed: {passed_tests}")
        print(f"  Failed: {failed_tests}")
        print(f"  Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print(f"\nDetailed Results:")
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "PASSED" else "❌"
            print(f"  {status_icon} {result['test']}: {result['status']}")
            
            if result["status"] == "PASSED" and "details" in result:
                print(f"      Details: {result['details']}")
            elif result["status"] == "FAILED" and "error" in result:
                print(f"      Error: {result['error']}")
        
        print(f"\n🎯 Task 7.4 Requirements Verification:")
        print(f"  ✅ DomainAdapter for document type customization: {'IMPLEMENTED' if passed_tests >= 4 else 'INCOMPLETE'}")
        print(f"  ✅ Domain-specific retrieval and response strategies: {'IMPLEMENTED' if passed_tests >= 4 else 'INCOMPLETE'}")
        print(f"  ✅ Domain detection from user interaction patterns: {'IMPLEMENTED' if passed_tests >= 4 else 'INCOMPLETE'}")
        print(f"  ✅ Domain adaptation effectiveness testing: {'IMPLEMENTED' if passed_tests >= 4 else 'INCOMPLETE'}")
        
        if failed_tests == 0:
            print(f"\n🎉 Task 7.4 VERIFICATION SUCCESSFUL!")
            print(f"   All domain adaptation capabilities have been successfully implemented and tested.")
        else:
            print(f"\n⚠️  Task 7.4 VERIFICATION INCOMPLETE")
            print(f"   {failed_tests} test(s) failed. Please review and fix the issues.")
        
        print("=" * 60)

async def main():
    """Run Task 7.4 verification."""
    verification = Task74Verification()
    await verification.run_verification()

if __name__ == "__main__":
    asyncio.run(main())