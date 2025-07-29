"""
Database configuration and initialization
"""
import asyncio
from sqlalchemy import create_engine, Column, String, DateTime, Text, Integer, Float, Boolean, ForeignKey, JSON, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from core.config import settings

# Create engine
engine = create_engine(settings.DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())
    last_login = Column(DateTime)
    is_active = Column(Boolean, default=True)

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    size = Column(Integer, nullable=False)
    status = Column(String, default="processing")  # processing, completed, failed
    chunks_count = Column(Integer, default=0)
    embeddings_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, nullable=False)
    role = Column(String, nullable=False)  # user, assistant
    content = Column(Text, nullable=False)
    sources = Column(Text)  # JSON string
    message_metadata = Column(Text)  # JSON string
    created_at = Column(DateTime, default=func.now())

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer)
    chunk_metadata = Column(Text)  # JSON string
    created_at = Column(DateTime, default=func.now())

# Enhanced Database Models for Advanced RAG Features

class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    preferences = Column(JSON)
    interaction_history = Column(JSON)
    domain_expertise = Column(JSON)
    learning_style = Column(String(50))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class DocumentChunkEnhanced(Base):
    __tablename__ = "document_chunks_enhanced"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    parent_chunk_id = Column(String, ForeignKey("document_chunks_enhanced.id"))
    content = Column(Text, nullable=False)
    chunk_level = Column(Integer, default=0)
    chunk_index = Column(Integer)
    overlap_start = Column(Integer)
    overlap_end = Column(Integer)
    sentence_boundaries = Column(Text)  # JSON array as text for SQLite compatibility
    chunk_metadata = Column(JSON)
    created_at = Column(DateTime, default=func.now())

class KnowledgeGraphEntity(Base):
    __tablename__ = "kg_entities"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    type = Column(String(100))
    description = Column(Text)
    importance_score = Column(Float, default=0.0)
    document_id = Column(String, ForeignKey("documents.id"))
    entity_metadata = Column(JSON)
    created_at = Column(DateTime, default=func.now())

class KnowledgeGraphRelationship(Base):
    __tablename__ = "kg_relationships"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source_entity_id = Column(String, ForeignKey("kg_entities.id"), nullable=False)
    target_entity_id = Column(String, ForeignKey("kg_entities.id"), nullable=False)
    relationship_type = Column(String(100))
    confidence_score = Column(Float)
    context = Column(Text)
    relationship_metadata = Column(JSON)
    created_at = Column(DateTime, default=func.now())

class ConversationMemory(Base):
    __tablename__ = "conversation_memory"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    memory_type = Column(String(50))  # 'short_term', 'long_term', 'context'
    content = Column(Text)
    importance_score = Column(Float)
    timestamp = Column(DateTime, default=func.now())
    expires_at = Column(DateTime)
    memory_metadata = Column(JSON)

class UserFeedback(Base):
    __tablename__ = "user_feedback"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    message_id = Column(String, ForeignKey("messages.id"))
    feedback_type = Column(String(50))  # 'rating', 'correction', 'preference'
    feedback_value = Column(JSON)
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    event_type = Column(String(100))
    event_data = Column(JSON)
    timestamp = Column(DateTime, default=func.now())
    session_id = Column(String(255))

class DocumentTag(Base):
    __tablename__ = "document_tags"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    tag_name = Column(String(100))
    tag_type = Column(String(50))  # 'topic', 'domain', 'sentiment', 'complexity'
    confidence_score = Column(Float)
    generated_by = Column(String(50))  # 'llm', 'rule_based', 'user'
    created_at = Column(DateTime, default=func.now())

async def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()