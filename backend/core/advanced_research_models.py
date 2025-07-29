"""
Advanced Research Ecosystem Database Models
Extended database models for the comprehensive research ecosystem including
research memory, planning, quality assurance, multilingual support, impact prediction,
ethics compliance, funding assistance, reproducibility, trend analysis, and collaboration.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from core.database import Base

# Research Context and Memory Models
class ResearchProject(Base):
    """Research project with persistent context"""
    __tablename__ = "research_projects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    research_domain = Column(String(200))
    status = Column(String(50), default="active")  # active, paused, completed, archived
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    contexts = relationship("ResearchContext", back_populates="project")
    roadmaps = relationship("ResearchRoadmap", back_populates="project")
    qa_reports = relationship("QAReport", back_populates="project")
    ethics_records = relationship("EthicsRecord", back_populates="project")
    funding_applications = relationship("FundingApplication", back_populates="project")
    collaborations = relationship("ResearchCollaboration", back_populates="project")

class ResearchContext(Base):
    """Persistent research context for sessions"""
    __tablename__ = "research_contexts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("research_projects.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    session_id = Column(String(100))
    active_documents = Column(JSON)  # List of document IDs
    current_queries = Column(JSON)   # List of recent queries
    research_focus = Column(Text)    # Current research focus area
    insights_generated = Column(JSON)  # List of insights
    context_metadata = Column(JSON)  # Additional context data
    session_timestamp = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    project = relationship("ResearchProject", back_populates="contexts")

class ResearchTimeline(Base):
    """Research timeline and history tracking"""
    __tablename__ = "research_timelines"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("research_projects.id"), nullable=False)
    event_type = Column(String(100), nullable=False)  # document_added, insight_generated, milestone_reached
    event_description = Column(Text)
    event_data = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)

# Research Planning Models
class ResearchRoadmap(Base):
    """AI-generated research roadmaps"""
    __tablename__ = "research_roadmaps"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("research_projects.id"), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    phases = Column(JSON)  # List of research phases
    estimated_duration_months = Column(Integer)
    resource_requirements = Column(JSON)
    risk_assessment = Column(JSON)
    success_metrics = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    project = relationship("ResearchProject", back_populates="roadmaps")
    milestones = relationship("ResearchMilestone", back_populates="roadmap")

class ResearchMilestone(Base):
    """Research milestones and progress tracking"""
    __tablename__ = "research_milestones"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    roadmap_id = Column(UUID(as_uuid=True), ForeignKey("research_roadmaps.id"), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    phase = Column(String(100))
    target_date = Column(DateTime)
    completion_date = Column(DateTime)
    status = Column(String(50), default="pending")  # pending, in_progress, completed, delayed
    progress_percentage = Column(Float, default=0.0)
    dependencies = Column(JSON)  # List of dependent milestone IDs
    deliverables = Column(JSON)  # Expected deliverables
    
    # Relationships
    roadmap = relationship("ResearchRoadmap", back_populates="milestones")

# Quality Assurance Models
class QAReport(Base):
    """Research quality assurance reports"""
    __tablename__ = "qa_reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("research_projects.id"), nullable=False)
    report_type = Column(String(100), nullable=False)  # methodology, statistical, bias, citation
    methodology_score = Column(Float)
    statistical_validity_score = Column(Float)
    bias_risk_score = Column(Float)
    citation_accuracy_score = Column(Float)
    overall_quality_score = Column(Float)
    issues_identified = Column(JSON)
    recommendations = Column(JSON)
    validation_details = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("ResearchProject", back_populates="qa_reports")

class ReproducibilityRecord(Base):
    """Research reproducibility tracking"""
    __tablename__ = "reproducibility_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("research_projects.id"), nullable=False)
    methodology_documentation = Column(JSON)
    code_repository_url = Column(String(500))
    data_availability = Column(JSON)
    environment_snapshot = Column(JSON)
    reproducibility_score = Column(Float)
    validation_results = Column(JSON)
    replication_package_url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Multilingual Support Models
class TranslationCache(Base):
    """Cache for research context translations"""
    __tablename__ = "translation_cache"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_text_hash = Column(String(64), nullable=False)  # SHA-256 hash
    source_language = Column(String(10), nullable=False)
    target_language = Column(String(10), nullable=False)
    translated_text = Column(Text, nullable=False)
    research_context = Column(JSON)  # Context used for translation
    translation_quality_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

class CulturalAdaptation(Base):
    """Cultural adaptations for research methodologies"""
    __tablename__ = "cultural_adaptations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    methodology_type = Column(String(200), nullable=False)
    source_culture = Column(String(50), nullable=False)
    target_culture = Column(String(50), nullable=False)
    adaptations = Column(JSON)  # List of cultural adaptations
    validation_status = Column(String(50))
    expert_reviewed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# Impact Prediction Models
class ImpactPrediction(Base):
    """Research impact predictions"""
    __tablename__ = "impact_predictions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("research_projects.id"), nullable=False)
    citation_potential = Column(Float)
    influence_score = Column(Float)
    novelty_assessment = Column(Float)
    significance_rating = Column(Float)
    predicted_citations_1year = Column(Integer)
    predicted_citations_5year = Column(Integer)
    confidence_interval_low = Column(Float)
    confidence_interval_high = Column(Float)
    prediction_factors = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class JournalRecommendation(Base):
    """Journal publication recommendations"""
    __tablename__ = "journal_recommendations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("research_projects.id"), nullable=False)
    journal_name = Column(String(500), nullable=False)
    impact_factor = Column(Float)
    acceptance_probability = Column(Float)
    fit_score = Column(Float)
    review_time_estimate_days = Column(Integer)
    recommendation_reasoning = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

# Ethics and Compliance Models
class EthicsRecord(Base):
    """Research ethics and compliance records"""
    __tablename__ = "ethics_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("research_projects.id"), nullable=False)
    ethics_requirements = Column(JSON)  # List of applicable requirements
    irb_required = Column(Boolean, default=False)
    irb_approval_status = Column(String(50))  # pending, approved, rejected, not_required
    consent_forms_generated = Column(JSON)
    compliance_status = Column(String(50), default="pending")
    regulatory_frameworks = Column(JSON)  # GDPR, HIPAA, etc.
    risk_assessment = Column(JSON)
    monitoring_schedule = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("ResearchProject", back_populates="ethics_records")

class ComplianceMonitoring(Base):
    """Ongoing compliance monitoring"""
    __tablename__ = "compliance_monitoring"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ethics_record_id = Column(UUID(as_uuid=True), ForeignKey("ethics_records.id"), nullable=False)
    check_type = Column(String(100), nullable=False)
    check_result = Column(String(50))  # compliant, non_compliant, warning
    issues_found = Column(JSON)
    corrective_actions = Column(JSON)
    next_check_date = Column(DateTime)
    checked_at = Column(DateTime, default=datetime.utcnow)

# Funding and Grant Models
class FundingOpportunity(Base):
    """Available funding opportunities"""
    __tablename__ = "funding_opportunities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    funding_agency = Column(String(200), nullable=False)
    program_name = Column(String(300))
    description = Column(Text)
    eligibility_criteria = Column(JSON)
    funding_amount_min = Column(Integer)
    funding_amount_max = Column(Integer)
    application_deadline = Column(DateTime)
    research_areas = Column(JSON)  # List of applicable research areas
    success_rate = Column(Float)
    average_award_amount = Column(Integer)
    review_criteria = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class FundingApplication(Base):
    """Grant applications and tracking"""
    __tablename__ = "funding_applications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("research_projects.id"), nullable=False)
    opportunity_id = Column(UUID(as_uuid=True), ForeignKey("funding_opportunities.id"), nullable=False)
    application_status = Column(String(50), default="draft")  # draft, submitted, under_review, awarded, rejected
    requested_amount = Column(Integer)
    proposal_draft = Column(Text)
    budget_breakdown = Column(JSON)
    success_probability = Column(Float)
    submission_date = Column(DateTime)
    decision_date = Column(DateTime)
    feedback_received = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("ResearchProject", back_populates="funding_applications")
    opportunity = relationship("FundingOpportunity")

# Trend Analysis Models
class ResearchTrend(Base):
    """Identified research trends"""
    __tablename__ = "research_trends"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trend_name = Column(String(300), nullable=False)
    research_domain = Column(String(200))
    trend_type = Column(String(100))  # emerging, declining, stable, breakthrough
    growth_rate = Column(Float)
    significance_score = Column(Float)
    key_concepts = Column(JSON)
    related_technologies = Column(JSON)
    predicted_impact = Column(JSON)
    time_horizon = Column(String(50))  # short_term, medium_term, long_term
    confidence_score = Column(Float)
    identified_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class FieldConvergence(Base):
    """Detected field convergences"""
    __tablename__ = "field_convergences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    convergence_name = Column(String(300), nullable=False)
    participating_fields = Column(JSON)  # List of converging fields
    convergence_strength = Column(Float)
    breakthrough_potential = Column(Float)
    key_technologies = Column(JSON)
    research_opportunities = Column(JSON)
    timeline_prediction = Column(JSON)
    identified_at = Column(DateTime, default=datetime.utcnow)

class OpportunityAlert(Base):
    """Research opportunity alerts"""
    __tablename__ = "opportunity_alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    alert_type = Column(String(100), nullable=False)  # trend, convergence, funding, collaboration
    title = Column(String(500), nullable=False)
    description = Column(Text)
    opportunity_data = Column(JSON)
    relevance_score = Column(Float)
    urgency_level = Column(String(50))  # low, medium, high, critical
    expiration_date = Column(DateTime)
    status = Column(String(50), default="active")  # active, dismissed, acted_upon
    created_at = Column(DateTime, default=datetime.utcnow)

# Collaboration Models
class ResearcherProfile(Base):
    """Extended researcher profiles for collaboration"""
    __tablename__ = "researcher_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    research_interests = Column(JSON)  # List of research interests
    expertise_areas = Column(JSON)    # List of expertise areas with proficiency levels
    collaboration_preferences = Column(JSON)
    publication_history = Column(JSON)
    h_index = Column(Integer)
    collaboration_success_rate = Column(Float)
    preferred_collaboration_types = Column(JSON)
    availability_status = Column(String(50), default="available")
    location = Column(String(200))
    institution = Column(String(300))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CollaborationMatch(Base):
    """Collaboration matching results"""
    __tablename__ = "collaboration_matches"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requester_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    matched_researcher_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    match_score = Column(Float, nullable=False)
    expertise_complementarity = Column(Float)
    collaboration_success_probability = Column(Float)
    shared_interests = Column(JSON)
    complementary_skills = Column(JSON)
    match_reasoning = Column(JSON)
    match_type = Column(String(100))  # expertise_based, interest_based, cross_disciplinary
    status = Column(String(50), default="suggested")  # suggested, contacted, accepted, declined
    created_at = Column(DateTime, default=datetime.utcnow)

class ResearchCollaboration(Base):
    """Active research collaborations"""
    __tablename__ = "research_collaborations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("research_projects.id"), nullable=False)
    collaboration_type = Column(String(100))  # internal, external, cross_disciplinary
    participants = Column(JSON)  # List of participant user IDs and roles
    collaboration_agreement = Column(JSON)
    communication_preferences = Column(JSON)
    shared_resources = Column(JSON)
    progress_tracking = Column(JSON)
    conflict_resolution_history = Column(JSON)
    success_metrics = Column(JSON)
    status = Column(String(50), default="active")  # active, paused, completed, terminated
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("ResearchProject", back_populates="collaborations")

class CollaborationConflict(Base):
    """Collaboration conflict tracking and resolution"""
    __tablename__ = "collaboration_conflicts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    collaboration_id = Column(UUID(as_uuid=True), ForeignKey("research_collaborations.id"), nullable=False)
    conflict_type = Column(String(100))  # methodology, authorship, resource, timeline
    description = Column(Text)
    involved_parties = Column(JSON)  # List of user IDs involved in conflict
    severity_level = Column(String(50))  # low, medium, high, critical
    resolution_strategy = Column(JSON)
    resolution_status = Column(String(50), default="open")  # open, in_progress, resolved, escalated
    mediator_assigned = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    resolution_notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)

# Association tables for many-to-many relationships
research_project_tags = Table(
    'research_project_tags',
    Base.metadata,
    Column('project_id', UUID(as_uuid=True), ForeignKey('research_projects.id'), primary_key=True),
    Column('tag_id', UUID(as_uuid=True), ForeignKey('document_tags.id'), primary_key=True)
)

funding_opportunity_areas = Table(
    'funding_opportunity_areas',
    Base.metadata,
    Column('opportunity_id', UUID(as_uuid=True), ForeignKey('funding_opportunities.id'), primary_key=True),
    Column('research_area', String(200), primary_key=True)
)

researcher_expertise = Table(
    'researcher_expertise',
    Base.metadata,
    Column('profile_id', UUID(as_uuid=True), ForeignKey('researcher_profiles.id'), primary_key=True),
    Column('expertise_area', String(200), primary_key=True),
    Column('proficiency_level', Float)  # 0.0 to 1.0
)