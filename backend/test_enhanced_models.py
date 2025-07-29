#!/usr/bin/env python3
"""
Test enhanced database models and schemas
"""
import asyncio
import sys
import os
import json
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import (
    SessionLocal, User, Document, Conversation, Message,
    UserProfile, DocumentChunkEnhanced, KnowledgeGraphEntity,
    KnowledgeGraphRelationship, ConversationMemory, UserFeedback,
    AnalyticsEvent, DocumentTag
)
from models.schemas import (
    UserProfileCreate, UserPreferences,
    DocumentChunkEnhancedCreate, KnowledgeGraphEntityCreate,
    KnowledgeGraphRelationshipCreate, ConversationMemoryCreate,
    UserFeedbackCreate, AnalyticsEventCreate, DocumentTagCreate,
    EntityType, RelationshipType, MemoryType, FeedbackType, TagType
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_models():
    """Test all enhanced database models"""
    db = SessionLocal()
    
    try:
        logger.info("Testing enhanced database models...")
        
        # Create a test user
        test_user = User(
            email="test@example.com",
            name="Test User",
            hashed_password="hashed_password_123"
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        logger.info(f"✓ Created test user: {test_user.id}")
        
        # Create a test document
        test_document = Document(
            user_id=test_user.id,
            name="Test Document",
            file_path="/test/path/document.pdf",
            content_type="application/pdf",
            size=1024,
            status="completed"
        )
        db.add(test_document)
        db.commit()
        db.refresh(test_document)
        logger.info(f"✓ Created test document: {test_document.id}")
        
        # Create a test conversation
        test_conversation = Conversation(
            user_id=test_user.id,
            title="Test Conversation"
        )
        db.add(test_conversation)
        db.commit()
        db.refresh(test_conversation)
        logger.info(f"✓ Created test conversation: {test_conversation.id}")
        
        # Test UserProfile
        test_user_profile = UserProfile(
            user_id=test_user.id,
            preferences={
                "language": "en",
                "response_style": "detailed",
                "domain_focus": ["AI", "ML"]
            },
            interaction_history={
                "total_queries": 10,
                "favorite_topics": ["machine learning", "neural networks"]
            },
            domain_expertise={
                "AI": 0.8,
                "ML": 0.7,
                "NLP": 0.6
            },
            learning_style="visual"
        )
        db.add(test_user_profile)
        db.commit()
        db.refresh(test_user_profile)
        logger.info(f"✓ Created user profile: {test_user_profile.id}")
        
        # Test DocumentChunkEnhanced
        test_chunk = DocumentChunkEnhanced(
            document_id=test_document.id,
            content="This is a test chunk with hierarchical structure.",
            chunk_level=0,
            chunk_index=1,
            overlap_start=0,
            overlap_end=10,
            sentence_boundaries=json.dumps([0, 25, 50]),
            chunk_metadata={
                "page_number": 1,
                "section": "introduction",
                "importance": 0.8
            }
        )
        db.add(test_chunk)
        db.commit()
        db.refresh(test_chunk)
        logger.info(f"✓ Created enhanced chunk: {test_chunk.id}")
        
        # Test child chunk
        test_child_chunk = DocumentChunkEnhanced(
            document_id=test_document.id,
            parent_chunk_id=test_chunk.id,
            content="This is a child chunk.",
            chunk_level=1,
            chunk_index=1,
            chunk_metadata={"child_of": test_chunk.id}
        )
        db.add(test_child_chunk)
        db.commit()
        db.refresh(test_child_chunk)
        logger.info(f"✓ Created child chunk: {test_child_chunk.id}")
        
        # Test KnowledgeGraphEntity
        test_entity1 = KnowledgeGraphEntity(
            name="Machine Learning",
            type="concept",
            description="A subset of artificial intelligence",
            importance_score=0.9,
            document_id=test_document.id,
            entity_metadata={
                "category": "technology",
                "related_fields": ["AI", "statistics", "computer science"]
            }
        )
        db.add(test_entity1)
        
        test_entity2 = KnowledgeGraphEntity(
            name="Neural Networks",
            type="concept",
            description="Computing systems inspired by biological neural networks",
            importance_score=0.8,
            document_id=test_document.id,
            entity_metadata={
                "category": "technology",
                "complexity": "high"
            }
        )
        db.add(test_entity2)
        db.commit()
        db.refresh(test_entity1)
        db.refresh(test_entity2)
        logger.info(f"✓ Created knowledge graph entities: {test_entity1.id}, {test_entity2.id}")
        
        # Test KnowledgeGraphRelationship
        test_relationship = KnowledgeGraphRelationship(
            source_entity_id=test_entity1.id,
            target_entity_id=test_entity2.id,
            relationship_type="related_to",
            confidence_score=0.85,
            context="Neural networks are a key component of machine learning",
            relationship_metadata={
                "strength": "strong",
                "bidirectional": True
            }
        )
        db.add(test_relationship)
        db.commit()
        db.refresh(test_relationship)
        logger.info(f"✓ Created knowledge graph relationship: {test_relationship.id}")
        
        # Test ConversationMemory
        test_memory = ConversationMemory(
            conversation_id=test_conversation.id,
            memory_type="short_term",
            content="User is interested in machine learning concepts",
            importance_score=0.7,
            expires_at=datetime.now() + timedelta(hours=24),
            memory_metadata={
                "topic": "machine learning",
                "sentiment": "positive"
            }
        )
        db.add(test_memory)
        db.commit()
        db.refresh(test_memory)
        logger.info(f"✓ Created conversation memory: {test_memory.id}")
        
        # Test UserFeedback
        test_feedback = UserFeedback(
            user_id=test_user.id,
            feedback_type="rating",
            feedback_value={
                "rating": 5,
                "comment": "Very helpful response",
                "aspects": {
                    "accuracy": 5,
                    "relevance": 4,
                    "clarity": 5
                }
            }
        )
        db.add(test_feedback)
        db.commit()
        db.refresh(test_feedback)
        logger.info(f"✓ Created user feedback: {test_feedback.id}")
        
        # Test AnalyticsEvent
        test_analytics = AnalyticsEvent(
            user_id=test_user.id,
            event_type="query_executed",
            event_data={
                "query": "What is machine learning?",
                "response_time": 0.5,
                "sources_count": 3,
                "satisfaction": 5
            },
            session_id="session_123"
        )
        db.add(test_analytics)
        db.commit()
        db.refresh(test_analytics)
        logger.info(f"✓ Created analytics event: {test_analytics.id}")
        
        # Test DocumentTag
        test_tag = DocumentTag(
            document_id=test_document.id,
            tag_name="artificial intelligence",
            tag_type="topic",
            confidence_score=0.9,
            generated_by="llm"
        )
        db.add(test_tag)
        db.commit()
        db.refresh(test_tag)
        logger.info(f"✓ Created document tag: {test_tag.id}")
        
        # Test queries
        logger.info("Testing database queries...")
        
        # Query user profile
        user_profile = db.query(UserProfile).filter(UserProfile.user_id == test_user.id).first()
        assert user_profile is not None
        assert user_profile.learning_style == "visual"
        logger.info("✓ User profile query successful")
        
        # Query hierarchical chunks
        parent_chunks = db.query(DocumentChunkEnhanced).filter(
            DocumentChunkEnhanced.document_id == test_document.id,
            DocumentChunkEnhanced.chunk_level == 0
        ).all()
        assert len(parent_chunks) == 1
        logger.info("✓ Hierarchical chunk query successful")
        
        # Query knowledge graph entities
        entities = db.query(KnowledgeGraphEntity).filter(
            KnowledgeGraphEntity.document_id == test_document.id
        ).all()
        assert len(entities) == 2
        logger.info("✓ Knowledge graph entity query successful")
        
        # Query relationships
        relationships = db.query(KnowledgeGraphRelationship).filter(
            KnowledgeGraphRelationship.source_entity_id == test_entity1.id
        ).all()
        assert len(relationships) == 1
        logger.info("✓ Knowledge graph relationship query successful")
        
        # Query conversation memory
        memories = db.query(ConversationMemory).filter(
            ConversationMemory.conversation_id == test_conversation.id
        ).all()
        assert len(memories) == 1
        logger.info("✓ Conversation memory query successful")
        
        # Query analytics events
        events = db.query(AnalyticsEvent).filter(
            AnalyticsEvent.user_id == test_user.id
        ).all()
        assert len(events) == 1
        logger.info("✓ Analytics event query successful")
        
        logger.info("✓ All database model tests passed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Database model test failed: {e}")
        return False
    finally:
        db.close()

def test_pydantic_schemas():
    """Test Pydantic schema validation"""
    try:
        logger.info("Testing Pydantic schemas...")
        
        # Test UserPreferences
        preferences = UserPreferences(
            language="en",
            response_style="detailed",
            domain_focus=["AI", "ML"],
            citation_preference="inline",
            reasoning_display=True,
            uncertainty_tolerance=0.5
        )
        assert preferences.language == "en"
        logger.info("✓ UserPreferences schema validation successful")
        
        # Test UserProfileCreate
        profile_create = UserProfileCreate(
            user_id="test_user_123",
            preferences=preferences,
            learning_style="visual",
            domain_expertise={"AI": 0.8, "ML": 0.7}
        )
        assert profile_create.user_id == "test_user_123"
        logger.info("✓ UserProfileCreate schema validation successful")
        
        # Test DocumentChunkEnhancedCreate
        chunk_create = DocumentChunkEnhancedCreate(
            document_id="doc_123",
            content="Test chunk content",
            chunk_level=0,
            chunk_index=1,
            overlap_start=0,
            overlap_end=10,
            sentence_boundaries=[0, 25, 50],
            metadata={"page": 1}
        )
        assert chunk_create.chunk_level == 0
        logger.info("✓ DocumentChunkEnhancedCreate schema validation successful")
        
        # Test KnowledgeGraphEntityCreate
        entity_create = KnowledgeGraphEntityCreate(
            name="Test Entity",
            type=EntityType.CONCEPT,
            description="A test entity",
            importance_score=0.8,
            metadata={"category": "test"}
        )
        assert entity_create.type == EntityType.CONCEPT
        logger.info("✓ KnowledgeGraphEntityCreate schema validation successful")
        
        # Test KnowledgeGraphRelationshipCreate
        relationship_create = KnowledgeGraphRelationshipCreate(
            source_entity_id="entity_1",
            target_entity_id="entity_2",
            relationship_type=RelationshipType.RELATED_TO,
            confidence_score=0.9,
            context="Test relationship",
            metadata={"strength": "strong"}
        )
        assert relationship_create.relationship_type == RelationshipType.RELATED_TO
        logger.info("✓ KnowledgeGraphRelationshipCreate schema validation successful")
        
        # Test ConversationMemoryCreate
        memory_create = ConversationMemoryCreate(
            conversation_id="conv_123",
            memory_type=MemoryType.SHORT_TERM,
            content="Test memory content",
            importance_score=0.7,
            metadata={"topic": "test"}
        )
        assert memory_create.memory_type == MemoryType.SHORT_TERM
        logger.info("✓ ConversationMemoryCreate schema validation successful")
        
        # Test UserFeedbackCreate
        feedback_create = UserFeedbackCreate(
            user_id="user_123",
            feedback_type=FeedbackType.RATING,
            feedback_value={"rating": 5, "comment": "Great!"}
        )
        assert feedback_create.feedback_type == FeedbackType.RATING
        logger.info("✓ UserFeedbackCreate schema validation successful")
        
        # Test AnalyticsEventCreate
        analytics_create = AnalyticsEventCreate(
            user_id="user_123",
            event_type="test_event",
            event_data={"action": "test", "value": 123},
            session_id="session_123"
        )
        assert analytics_create.event_type == "test_event"
        logger.info("✓ AnalyticsEventCreate schema validation successful")
        
        # Test DocumentTagCreate
        tag_create = DocumentTagCreate(
            document_id="doc_123",
            tag_name="test_tag",
            tag_type=TagType.TOPIC,
            confidence_score=0.9,
            generated_by="system"
        )
        assert tag_create.tag_type == TagType.TOPIC
        logger.info("✓ DocumentTagCreate schema validation successful")
        
        logger.info("✓ All Pydantic schema tests passed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Pydantic schema test failed: {e}")
        return False

def main():
    """Main test function"""
    logger.info("Starting enhanced database and schema tests...")
    
    # Test database models
    db_success = test_database_models()
    
    # Test Pydantic schemas
    schema_success = test_pydantic_schemas()
    
    if db_success and schema_success:
        logger.info("All enhanced database and schema tests completed successfully!")
        sys.exit(0)
    else:
        logger.error("Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()