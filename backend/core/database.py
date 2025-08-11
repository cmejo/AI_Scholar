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

# Educational Enhancement System Models

class Quiz(Base):
    __tablename__ = "quizzes"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    description = Column(Text)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    difficulty_level = Column(String(50))  # 'beginner', 'intermediate', 'advanced'
    estimated_time_minutes = Column(Integer)
    learning_objectives = Column(Text)  # JSON array as text
    created_at = Column(DateTime, default=func.now())
    quiz_metadata = Column(JSON)

class QuizQuestion(Base):
    __tablename__ = "quiz_questions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    quiz_id = Column(String, ForeignKey("quizzes.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50))  # 'multiple_choice', 'short_answer', 'essay', etc.
    difficulty_level = Column(String(50))
    options = Column(Text)  # JSON array as text for multiple choice options
    correct_answer = Column(Text)
    explanation = Column(Text)
    source_content = Column(Text)
    confidence_score = Column(Float)
    learning_objectives = Column(Text)  # JSON array as text
    question_metadata = Column(JSON)

class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    quiz_id = Column(String, ForeignKey("quizzes.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    started_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime)
    score = Column(Float)
    total_points = Column(Float)
    time_taken_minutes = Column(Integer)
    attempt_metadata = Column(JSON)

class QuizResponse(Base):
    __tablename__ = "quiz_responses"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    attempt_id = Column(String, ForeignKey("quiz_attempts.id"), nullable=False)
    question_id = Column(String, ForeignKey("quiz_questions.id"), nullable=False)
    user_answer = Column(Text)
    is_correct = Column(Boolean)
    points_earned = Column(Float)
    time_taken_seconds = Column(Integer)
    response_metadata = Column(JSON)

class StudySession(Base):
    __tablename__ = "study_sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    session_type = Column(String(50))  # 'quiz', 'review', 'practice'
    started_at = Column(DateTime, default=func.now())
    ended_at = Column(DateTime)
    items_studied = Column(Integer)
    performance_score = Column(Float)
    session_metadata = Column(JSON)

class LearningProgress(Base):
    __tablename__ = "learning_progress"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    topic = Column(String(255))
    competency_level = Column(Float)  # 0.0 to 1.0
    last_studied = Column(DateTime)
    study_count = Column(Integer, default=0)
    average_score = Column(Float)
    progress_metadata = Column(JSON)

class SpacedRepetitionItem(Base):
    __tablename__ = "spaced_repetition_items"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    content_id = Column(String)  # Can reference quiz questions, concepts, etc.
    content_type = Column(String(50))  # 'question', 'concept', 'fact'
    difficulty = Column(Float, default=2.5)  # SuperMemo difficulty factor
    interval = Column(Integer, default=1)  # Days until next review
    repetitions = Column(Integer, default=0)
    ease_factor = Column(Float, default=2.5)
    next_review_date = Column(DateTime)
    last_reviewed = Column(DateTime)
    sr_metadata = Column(JSON)

class Achievement(Base):
    __tablename__ = "achievements"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    achievement_type = Column(String(100))  # 'quiz_master', 'streak_keeper', etc.
    title = Column(String(255))
    description = Column(Text)
    earned_at = Column(DateTime, default=func.now())
    points = Column(Integer, default=0)
    achievement_metadata = Column(JSON)

# Enterprise Compliance and Institutional Models

class Institution(Base):
    __tablename__ = "institutions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    domain = Column(String(255))  # email domain for auto-assignment
    type = Column(String(100))  # 'university', 'research_institute', 'corporate'
    settings = Column(JSON)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class InstitutionalPolicy(Base):
    __tablename__ = "institutional_policies"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    institution_id = Column(String, ForeignKey("institutions.id"), nullable=False)
    policy_name = Column(String(255), nullable=False)
    policy_type = Column(String(100))  # 'research_ethics', 'data_usage', 'collaboration'
    description = Column(Text)
    rules = Column(JSON)  # Policy rules and conditions
    enforcement_level = Column(String(50))  # 'warning', 'blocking', 'reporting'
    is_active = Column(Boolean, default=True)
    effective_date = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class ComplianceViolation(Base):
    __tablename__ = "compliance_violations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    institution_id = Column(String, ForeignKey("institutions.id"), nullable=False)
    policy_id = Column(String, ForeignKey("institutional_policies.id"), nullable=False)
    violation_type = Column(String(100))
    severity = Column(String(50))  # 'low', 'medium', 'high', 'critical'
    description = Column(Text)
    context_data = Column(JSON)  # Additional context about the violation
    resolution_status = Column(String(50), default='open')  # 'open', 'acknowledged', 'resolved'
    resolution_notes = Column(Text)
    detected_at = Column(DateTime, default=func.now())
    resolved_at = Column(DateTime)

class UserRole(Base):
    __tablename__ = "user_roles"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    institution_id = Column(String, ForeignKey("institutions.id"), nullable=False)
    role_name = Column(String(100))  # 'student', 'faculty', 'admin', 'researcher'
    department = Column(String(255))
    permissions = Column(JSON)  # Role-specific permissions
    is_active = Column(Boolean, default=True)
    assigned_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime)

class ResourceUsage(Base):
    __tablename__ = "resource_usage"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    institution_id = Column(String, ForeignKey("institutions.id"), nullable=False)
    resource_type = Column(String(100))  # 'database_query', 'document_upload', 'ai_request'
    resource_name = Column(String(255))
    usage_amount = Column(Float)  # Quantity used
    usage_unit = Column(String(50))  # 'queries', 'mb', 'requests'
    cost = Column(Float)  # Associated cost if applicable
    timestamp = Column(DateTime, default=func.now())
    usage_metadata = Column(JSON)

class StudentProgress(Base):
    __tablename__ = "student_progress"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String, ForeignKey("users.id"), nullable=False)
    advisor_id = Column(String, ForeignKey("users.id"))
    institution_id = Column(String, ForeignKey("institutions.id"), nullable=False)
    research_project = Column(String(255))
    milestones = Column(JSON)  # Project milestones and deadlines
    progress_status = Column(String(50))  # 'on_track', 'behind', 'ahead'
    completion_percentage = Column(Float, default=0.0)
    last_update = Column(DateTime, default=func.now())
    notes = Column(Text)
    progress_metadata = Column(JSON)

class AdvisorFeedback(Base):
    __tablename__ = "advisor_feedback"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_progress_id = Column(String, ForeignKey("student_progress.id"), nullable=False)
    advisor_id = Column(String, ForeignKey("users.id"), nullable=False)
    feedback_type = Column(String(50))  # 'milestone_review', 'general_feedback', 'concern'
    feedback_text = Column(Text)
    rating = Column(Integer)  # 1-5 rating if applicable
    created_at = Column(DateTime, default=func.now())
    feedback_metadata = Column(JSON)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    institution_id = Column(String, ForeignKey("institutions.id"))
    action = Column(String(255))  # Action performed
    resource_type = Column(String(100))  # Type of resource accessed
    resource_id = Column(String(255))  # ID of the resource
    ip_address = Column(String(45))
    user_agent = Column(Text)
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    timestamp = Column(DateTime, default=func.now())
    audit_metadata = Column(JSON)

# Opportunity Matching and Discovery System Models

class ResearchProfile(Base):
    __tablename__ = "research_profiles"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    research_interests = Column(JSON)  # List of research topics/keywords
    expertise_areas = Column(JSON)  # Areas of expertise with proficiency levels
    research_domains = Column(JSON)  # Academic domains (e.g., computer science, biology)
    career_stage = Column(String(50))  # 'undergraduate', 'graduate', 'postdoc', 'faculty'
    institution_affiliation = Column(String(255))
    previous_funding = Column(JSON)  # History of previous grants/funding
    publications = Column(JSON)  # Publication history and metrics
    collaborators = Column(JSON)  # Frequent collaborators
    geographic_preferences = Column(JSON)  # Preferred funding regions/countries
    funding_amount_range = Column(JSON)  # Min/max funding amounts of interest
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class FundingOpportunity(Base):
    __tablename__ = "funding_opportunities"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(500), nullable=False)
    description = Column(Text)
    funding_agency = Column(String(255))
    program_name = Column(String(255))
    opportunity_type = Column(String(100))  # 'grant', 'fellowship', 'award', 'contract'
    funding_amount_min = Column(Float)
    funding_amount_max = Column(Float)
    duration_months = Column(Integer)
    eligibility_criteria = Column(JSON)  # Structured eligibility requirements
    research_areas = Column(JSON)  # Relevant research domains/topics
    keywords = Column(JSON)  # Keywords for matching
    application_deadline = Column(DateTime)
    award_date = Column(DateTime)
    application_url = Column(String(500))
    contact_info = Column(JSON)
    requirements = Column(JSON)  # Application requirements and documents needed
    restrictions = Column(JSON)  # Geographic, institutional, or other restrictions
    success_rate = Column(Float)  # Historical success rate if available
    average_award_amount = Column(Float)
    is_active = Column(Boolean, default=True)
    source = Column(String(100))  # Data source (e.g., 'nsf', 'nih', 'grants_gov')
    external_id = Column(String(255))  # ID from external source
    last_updated = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    opportunity_metadata = Column(JSON)

class FundingMatch(Base):
    __tablename__ = "funding_matches"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    funding_opportunity_id = Column(String, ForeignKey("funding_opportunities.id"), nullable=False)
    relevance_score = Column(Float, nullable=False)  # 0.0 to 1.0
    match_reasons = Column(JSON)  # Detailed reasons for the match
    keyword_matches = Column(JSON)  # Matching keywords and their weights
    eligibility_status = Column(String(50))  # 'eligible', 'potentially_eligible', 'not_eligible'
    recommendation_strength = Column(String(50))  # 'high', 'medium', 'low'
    created_at = Column(DateTime, default=func.now())
    last_updated = Column(DateTime, default=func.now(), onupdate=func.now())
    match_metadata = Column(JSON)

class FundingAlert(Base):
    __tablename__ = "funding_alerts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    alert_name = Column(String(255))
    search_criteria = Column(JSON)  # Criteria for matching opportunities
    notification_frequency = Column(String(50))  # 'immediate', 'daily', 'weekly'
    is_active = Column(Boolean, default=True)
    last_triggered = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    alert_metadata = Column(JSON)

class FundingNotification(Base):
    __tablename__ = "funding_notifications"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    funding_opportunity_id = Column(String, ForeignKey("funding_opportunities.id"), nullable=False)
    alert_id = Column(String, ForeignKey("funding_alerts.id"))
    notification_type = Column(String(50))  # 'new_opportunity', 'deadline_reminder', 'match_update'
    message = Column(Text)
    is_read = Column(Boolean, default=False)
    sent_at = Column(DateTime, default=func.now())
    notification_metadata = Column(JSON)

class GrantDatabase(Base):
    __tablename__ = "grant_databases"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    base_url = Column(String(500))
    api_endpoint = Column(String(500))
    authentication_type = Column(String(50))  # 'api_key', 'oauth', 'none'
    is_active = Column(Boolean, default=True)
    last_sync = Column(DateTime)
    sync_frequency_hours = Column(Integer, default=24)
    supported_fields = Column(JSON)  # Fields available from this database
    rate_limit = Column(JSON)  # Rate limiting information
    created_at = Column(DateTime, default=func.now())
    database_metadata = Column(JSON)

class PublicationVenue(Base):
    __tablename__ = "publication_venues"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    venue_type = Column(String(50))  # 'journal', 'conference', 'workshop'
    publisher = Column(String(255))
    issn = Column(String(20))  # For journals
    isbn = Column(String(20))  # For conference proceedings
    impact_factor = Column(Float)
    h_index = Column(Integer)
    acceptance_rate = Column(Float)  # Percentage
    research_areas = Column(JSON)  # List of research areas
    keywords = Column(JSON)  # Keywords for matching
    submission_frequency = Column(String(50))  # 'annual', 'biannual', 'quarterly', 'monthly'
    review_process = Column(String(50))  # 'peer_review', 'editorial_review', 'open_review'
    open_access = Column(Boolean, default=False)
    publication_fee = Column(Float)  # Publication fee if applicable
    average_review_time_days = Column(Integer)
    geographic_scope = Column(String(50))  # 'international', 'national', 'regional'
    language = Column(String(50), default='English')
    website_url = Column(String(500))
    submission_guidelines_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    last_updated = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    venue_metadata = Column(JSON)

class PublicationDeadline(Base):
    __tablename__ = "publication_deadlines"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    venue_id = Column(String, ForeignKey("publication_venues.id"), nullable=False)
    deadline_type = Column(String(50))  # 'abstract', 'full_paper', 'camera_ready'
    deadline_date = Column(DateTime, nullable=False)
    notification_date = Column(DateTime)
    publication_date = Column(DateTime)
    volume_issue = Column(String(50))  # For journals
    special_issue_theme = Column(String(255))  # For special issues
    submission_url = Column(String(500))
    additional_requirements = Column(JSON)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    deadline_metadata = Column(JSON)

class PublicationMatch(Base):
    __tablename__ = "publication_matches"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    venue_id = Column(String, ForeignKey("publication_venues.id"), nullable=False)
    paper_abstract = Column(Text)  # Abstract of the paper being matched
    relevance_score = Column(Float, nullable=False)  # 0.0 to 1.0
    match_reasons = Column(JSON)  # Detailed reasons for the match
    fit_score = Column(Float)  # How well the paper fits the venue
    success_probability = Column(Float)  # Predicted acceptance probability
    recommendation_strength = Column(String(50))  # 'high', 'medium', 'low'
    created_at = Column(DateTime, default=func.now())
    last_updated = Column(DateTime, default=func.now(), onupdate=func.now())
    match_metadata = Column(JSON)

class SubmissionTracker(Base):
    __tablename__ = "submission_tracker"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    venue_id = Column(String, ForeignKey("publication_venues.id"), nullable=False)
    paper_title = Column(String(500), nullable=False)
    paper_abstract = Column(Text)
    submission_date = Column(DateTime)
    deadline_id = Column(String, ForeignKey("publication_deadlines.id"))
    status = Column(String(50))  # 'planned', 'submitted', 'under_review', 'accepted', 'rejected', 'withdrawn'
    submission_id = Column(String(255))  # ID from the venue's submission system
    review_comments = Column(Text)
    decision_date = Column(DateTime)
    revision_deadline = Column(DateTime)
    final_decision = Column(String(50))  # 'accepted', 'rejected', 'major_revision', 'minor_revision'
    notes = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    submission_metadata = Column(JSON)

class GrantApplication(Base):
    __tablename__ = "grant_applications"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    funding_opportunity_id = Column(String, ForeignKey("funding_opportunities.id"), nullable=False)
    application_title = Column(String(500), nullable=False)
    project_description = Column(Text)
    requested_amount = Column(Float)
    project_duration_months = Column(Integer)
    application_deadline = Column(DateTime, nullable=False)
    submission_date = Column(DateTime)
    status = Column(String(50), default='draft')  # 'draft', 'submitted', 'under_review', 'awarded', 'rejected', 'withdrawn'
    external_application_id = Column(String(255))  # ID from funding agency system
    principal_investigator = Column(String(255))
    co_investigators = Column(JSON)  # List of co-investigators
    institution = Column(String(255))
    budget_breakdown = Column(JSON)  # Detailed budget information
    documents = Column(JSON)  # List of required documents and their status
    review_comments = Column(Text)
    decision_date = Column(DateTime)
    award_amount = Column(Float)  # Actual awarded amount if different from requested
    award_start_date = Column(DateTime)
    award_end_date = Column(DateTime)
    reporting_requirements = Column(JSON)  # Required reports and deadlines
    notes = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    application_metadata = Column(JSON)

class ApplicationDeadlineReminder(Base):
    __tablename__ = "application_deadline_reminders"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    application_id = Column(String, ForeignKey("grant_applications.id"), nullable=False)
    reminder_type = Column(String(50))  # 'deadline_approaching', 'document_due', 'report_due'
    reminder_date = Column(DateTime, nullable=False)
    message = Column(Text)
    is_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())

class ApplicationDocument(Base):
    __tablename__ = "application_documents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    application_id = Column(String, ForeignKey("grant_applications.id"), nullable=False)
    document_type = Column(String(100))  # 'proposal', 'budget', 'cv', 'letters_of_support', etc.
    document_name = Column(String(255))
    file_path = Column(String(500))
    version = Column(Integer, default=1)
    upload_date = Column(DateTime, default=func.now())
    is_required = Column(Boolean, default=True)
    is_submitted = Column(Boolean, default=False)
    file_size = Column(Integer)
    file_type = Column(String(50))
    created_at = Column(DateTime, default=func.now())
    document_metadata = Column(JSON)

class ApplicationCollaborator(Base):
    __tablename__ = "application_collaborators"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    application_id = Column(String, ForeignKey("grant_applications.id"), nullable=False)
    collaborator_name = Column(String(255), nullable=False)
    collaborator_email = Column(String(255))
    role = Column(String(100))  # 'co_investigator', 'consultant', 'student'
    institution = Column(String(255))
    contribution = Column(Text)
    is_confirmed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    collaborator_metadata = Column(JSON)

# Database session management
def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create all tables
def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)

# Initialize database
def init_db():
    """Initialize database with tables"""
    create_tables()
    print("Database initialized successfully")
    invited_at = Column(DateTime, default=func.now())
    responded_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    collaborator_metadata = Column(JSON)

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