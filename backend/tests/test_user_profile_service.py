"""
Tests for User Profile Management Service
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, patch

from core.database import Base, UserProfile, User, DocumentTag
from services.user_profile_service import UserProfileManager, InteractionTracker
from models.schemas import UserPreferences

# Test database setup
TEST_DATABASE_URL = "sqlite:///./test_user_profile.db"
test_engine = create_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture
def db_session():
    """Create test database session."""
    Base.metadata.create_all(bind=test_engine)
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def profile_manager(db_session):
    """Create UserProfileManager instance."""
    return UserProfileManager(db_session)

@pytest.fixture
def interaction_tracker(db_session):
    """Create InteractionTracker instance."""
    return InteractionTracker(db_session)

@pytest.fixture
def sample_user_id():
    """Sample user ID for testing."""
    return "test-user-123"

@pytest.fixture
def sample_preferences():
    """Sample user preferences."""
    return UserPreferences(
        language="en",
        response_style="detailed",
        domain_focus=["technology", "science"],
        citation_preference="inline",
        reasoning_display=True,
        uncertainty_tolerance=0.7
    )

class TestUserProfileManager:
    """Test cases for UserProfileManager."""
    
    @pytest.mark.asyncio
    async def test_create_user_profile_success(self, profile_manager, sample_user_id, sample_preferences):
        """Test successful user profile creation."""
        # Create profile
        profile = await profile_manager.create_user_profile(
            user_id=sample_user_id,
            preferences=sample_preferences,
            learning_style="visual"
        )
        
        # Verify profile creation
        assert profile.user_id == sample_user_id
        assert profile.preferences.language == "en"
        assert profile.preferences.response_style == "detailed"
        assert profile.learning_style == "visual"
        assert profile.domain_expertise == {}
        assert "total_queries" in profile.interaction_history
        assert profile.interaction_history["total_queries"] == 0
    
    @pytest.mark.asyncio
    async def test_create_user_profile_default_preferences(self, profile_manager, sample_user_id):
        """Test user profile creation with default preferences."""
        # Create profile without preferences
        profile = await profile_manager.create_user_profile(user_id=sample_user_id)
        
        # Verify default preferences
        assert profile.preferences.language == "en"
        assert profile.preferences.response_style == "detailed"
        assert profile.preferences.citation_preference == "inline"
        assert profile.learning_style == "visual"
    
    @pytest.mark.asyncio
    async def test_create_duplicate_profile(self, profile_manager, sample_user_id, sample_preferences):
        """Test creating duplicate profile returns existing profile."""
        # Create first profile
        profile1 = await profile_manager.create_user_profile(
            user_id=sample_user_id,
            preferences=sample_preferences
        )
        
        # Attempt to create duplicate
        profile2 = await profile_manager.create_user_profile(
            user_id=sample_user_id,
            preferences=sample_preferences
        )
        
        # Should return the same profile
        assert profile1.id == profile2.id
        assert profile1.user_id == profile2.user_id
    
    @pytest.mark.asyncio
    async def test_get_user_profile_exists(self, profile_manager, sample_user_id, sample_preferences):
        """Test getting existing user profile."""
        # Create profile
        created_profile = await profile_manager.create_user_profile(
            user_id=sample_user_id,
            preferences=sample_preferences
        )
        
        # Get profile
        retrieved_profile = await profile_manager.get_user_profile(sample_user_id)
        
        # Verify retrieval
        assert retrieved_profile is not None
        assert retrieved_profile.id == created_profile.id
        assert retrieved_profile.user_id == sample_user_id
    
    @pytest.mark.asyncio
    async def test_get_user_profile_not_exists(self, profile_manager):
        """Test getting non-existent user profile."""
        # Get non-existent profile
        profile = await profile_manager.get_user_profile("non-existent-user")
        
        # Should return None
        assert profile is None
    
    @pytest.mark.asyncio
    async def test_update_user_preferences(self, profile_manager, sample_user_id, sample_preferences):
        """Test updating user preferences."""
        # Create profile
        await profile_manager.create_user_profile(user_id=sample_user_id)
        
        # Update preferences
        new_preferences = UserPreferences(
            language="es",
            response_style="concise",
            domain_focus=["business"],
            citation_preference="footnote",
            reasoning_display=False,
            uncertainty_tolerance=0.3
        )
        
        updated_profile = await profile_manager.update_user_preferences(
            user_id=sample_user_id,
            preferences=new_preferences
        )
        
        # Verify updates
        assert updated_profile.preferences.language == "es"
        assert updated_profile.preferences.response_style == "concise"
        assert updated_profile.preferences.domain_focus == ["business"]
        assert updated_profile.preferences.citation_preference == "footnote"
        assert updated_profile.preferences.reasoning_display == False
        assert updated_profile.preferences.uncertainty_tolerance == 0.3
    
    @pytest.mark.asyncio
    async def test_update_preferences_creates_profile(self, profile_manager, sample_user_id, sample_preferences):
        """Test updating preferences creates profile if it doesn't exist."""
        # Update preferences for non-existent user
        updated_profile = await profile_manager.update_user_preferences(
            user_id=sample_user_id,
            preferences=sample_preferences
        )
        
        # Verify profile was created
        assert updated_profile.user_id == sample_user_id
        assert updated_profile.preferences.language == "en"
    
    @pytest.mark.asyncio
    async def test_track_query_interaction(self, profile_manager, sample_user_id):
        """Test tracking query interactions."""
        # Create profile
        await profile_manager.create_user_profile(user_id=sample_user_id)
        
        # Track query interaction
        await profile_manager.track_user_interaction(
            user_id=sample_user_id,
            interaction_type="query",
            interaction_data={
                "query": "What is machine learning?",
                "response_time": 2.5,
                "sources_used": 3,
                "satisfaction": 0.8
            }
        )
        
        # Verify tracking
        profile = await profile_manager.get_user_profile(sample_user_id)
        assert profile.interaction_history["total_queries"] == 1
        assert len(profile.interaction_history["query_history"]) == 1
        
        query_record = profile.interaction_history["query_history"][0]
        assert query_record["query"] == "What is machine learning?"
        assert query_record["response_time"] == 2.5
        assert query_record["sources_used"] == 3
        assert query_record["satisfaction"] == 0.8
    
    @pytest.mark.asyncio
    async def test_track_document_interaction(self, profile_manager, sample_user_id):
        """Test tracking document interactions."""
        # Create profile
        await profile_manager.create_user_profile(user_id=sample_user_id)
        
        # Track document interaction
        await profile_manager.track_user_interaction(
            user_id=sample_user_id,
            interaction_type="document",
            interaction_data={
                "document_id": "doc-123",
                "query_related": True
            }
        )
        
        # Verify tracking
        profile = await profile_manager.get_user_profile(sample_user_id)
        assert profile.interaction_history["total_documents"] == 1
        assert "doc-123" in profile.interaction_history["document_interactions"]
        
        doc_record = profile.interaction_history["document_interactions"]["doc-123"]
        assert doc_record["access_count"] == 1
        assert doc_record["queries_related"] == 1
    
    @pytest.mark.asyncio
    async def test_track_feedback_interaction(self, profile_manager, sample_user_id):
        """Test tracking feedback interactions."""
        # Create profile
        await profile_manager.create_user_profile(user_id=sample_user_id)
        
        # Track feedback interaction
        await profile_manager.track_user_interaction(
            user_id=sample_user_id,
            interaction_type="feedback",
            interaction_data={
                "feedback_type": "rating",
                "rating": 4.5,
                "message_id": "msg-123"
            }
        )
        
        # Verify tracking
        profile = await profile_manager.get_user_profile(sample_user_id)
        assert len(profile.interaction_history["feedback_history"]) == 1
        
        feedback_record = profile.interaction_history["feedback_history"][0]
        assert feedback_record["feedback_type"] == "rating"
        assert feedback_record["rating"] == 4.5
        assert feedback_record["message_id"] == "msg-123"
    
    @pytest.mark.asyncio
    async def test_analyze_user_behavior_insufficient_data(self, profile_manager, sample_user_id):
        """Test behavior analysis with insufficient data."""
        # Create profile without interactions
        await profile_manager.create_user_profile(user_id=sample_user_id)
        
        # Analyze behavior
        analysis = await profile_manager.analyze_user_behavior(sample_user_id)
        
        # Should indicate insufficient data
        assert analysis["analysis"] == "insufficient_data"
    
    @pytest.mark.asyncio
    async def test_analyze_user_behavior_with_data(self, profile_manager, sample_user_id):
        """Test behavior analysis with sufficient data."""
        # Create profile
        await profile_manager.create_user_profile(user_id=sample_user_id)
        
        # Add multiple query interactions
        for i in range(5):
            await profile_manager.track_user_interaction(
                user_id=sample_user_id,
                interaction_type="query",
                interaction_data={
                    "query": f"Test query {i} with varying length and complexity",
                    "response_time": 2.0 + i * 0.5,
                    "sources_used": 2 + i,
                    "satisfaction": 0.6 + i * 0.1
                }
            )
        
        # Analyze behavior
        analysis = await profile_manager.analyze_user_behavior(sample_user_id)
        
        # Verify analysis results
        assert "avg_response_time" in analysis
        assert "avg_query_length" in analysis
        assert "query_complexity" in analysis
        assert "avg_satisfaction" in analysis
        assert "total_interactions" in analysis
        assert "engagement_level" in analysis
        
        assert analysis["avg_response_time"] > 0
        assert analysis["query_complexity"] in ["low", "medium", "high"]
        assert analysis["engagement_level"] in ["low", "medium", "high"]
    
    @pytest.mark.asyncio
    async def test_get_domain_expertise_empty(self, profile_manager, sample_user_id):
        """Test getting domain expertise for new user."""
        # Create profile
        await profile_manager.create_user_profile(user_id=sample_user_id)
        
        # Get domain expertise
        expertise = await profile_manager.get_domain_expertise(sample_user_id)
        
        # Should be empty for new user
        assert expertise == {}
    
    @pytest.mark.asyncio
    async def test_get_domain_expertise_non_existent_user(self, profile_manager):
        """Test getting domain expertise for non-existent user."""
        # Get domain expertise for non-existent user
        expertise = await profile_manager.get_domain_expertise("non-existent-user")
        
        # Should return empty dict
        assert expertise == {}
    
    @pytest.mark.asyncio
    async def test_get_personalization_weights_default(self, profile_manager, sample_user_id):
        """Test getting personalization weights for new user."""
        # Create profile
        await profile_manager.create_user_profile(user_id=sample_user_id)
        
        # Get personalization weights
        weights = await profile_manager.get_personalization_weights(sample_user_id)
        
        # Verify default weights structure
        assert "response_style_weight" in weights
        assert "citation_weight" in weights
        assert "reasoning_weight" in weights
        assert "uncertainty_tolerance" in weights
        assert "domain_weights" in weights
        assert "satisfaction_weight" in weights
        assert "complexity_preference" in weights
        
        # Verify weight values are reasonable
        assert 0 <= weights["uncertainty_tolerance"] <= 1
        assert isinstance(weights["domain_weights"], dict)
    
    @pytest.mark.asyncio
    async def test_get_personalization_weights_non_existent_user(self, profile_manager):
        """Test getting personalization weights for non-existent user."""
        # Get weights for non-existent user
        weights = await profile_manager.get_personalization_weights("non-existent-user")
        
        # Should return default weights
        assert "response_style_weight" in weights
        assert weights["response_style_weight"] == 0.8  # Default value

class TestInteractionTracker:
    """Test cases for InteractionTracker."""
    
    @pytest.mark.asyncio
    async def test_track_query(self, interaction_tracker, sample_user_id):
        """Test tracking query through InteractionTracker."""
        # Track query
        await interaction_tracker.track_query(
            user_id=sample_user_id,
            query="What is artificial intelligence?",
            response_time=3.2,
            sources_used=4,
            satisfaction=0.9
        )
        
        # Verify tracking
        profile = await interaction_tracker.profile_manager.get_user_profile(sample_user_id)
        assert profile is not None
        assert profile.interaction_history["total_queries"] == 1
    
    @pytest.mark.asyncio
    async def test_track_document_access(self, interaction_tracker, sample_user_id):
        """Test tracking document access through InteractionTracker."""
        # Track document access
        await interaction_tracker.track_document_access(
            user_id=sample_user_id,
            document_id="doc-456",
            query_related=True
        )
        
        # Verify tracking
        profile = await interaction_tracker.profile_manager.get_user_profile(sample_user_id)
        assert profile is not None
        assert profile.interaction_history["total_documents"] == 1
        assert "doc-456" in profile.interaction_history["document_interactions"]
    
    @pytest.mark.asyncio
    async def test_track_feedback(self, interaction_tracker, sample_user_id):
        """Test tracking feedback through InteractionTracker."""
        # Track feedback
        await interaction_tracker.track_feedback(
            user_id=sample_user_id,
            feedback_type="rating",
            rating=4.0,
            message_id="msg-789"
        )
        
        # Verify tracking
        profile = await interaction_tracker.profile_manager.get_user_profile(sample_user_id)
        assert profile is not None
        assert len(profile.interaction_history["feedback_history"]) == 1

class TestDomainExpertiseDetection:
    """Test cases for domain expertise detection."""
    
    @pytest.mark.asyncio
    async def test_domain_expertise_from_queries(self, profile_manager, sample_user_id, db_session):
        """Test domain expertise detection from query patterns."""
        # Create profile
        await profile_manager.create_user_profile(user_id=sample_user_id)
        
        # Add technology-related queries
        tech_queries = [
            "How does machine learning work?",
            "What is software architecture?",
            "Explain data structures and algorithms",
            "Programming best practices",
            "Computer vision techniques"
        ]
        
        for query in tech_queries:
            await profile_manager.track_user_interaction(
                user_id=sample_user_id,
                interaction_type="query",
                interaction_data={
                    "query": query,
                    "response_time": 2.0,
                    "sources_used": 3
                }
            )
        
        # Get domain expertise
        expertise = await profile_manager.get_domain_expertise(sample_user_id)
        
        # Should detect technology domain
        assert "technology" in expertise
        assert expertise["technology"] > 0
    
    @pytest.mark.asyncio
    async def test_domain_expertise_from_document_tags(self, profile_manager, sample_user_id, db_session):
        """Test domain expertise detection from document interactions."""
        # Create profile
        await profile_manager.create_user_profile(user_id=sample_user_id)
        
        # Create mock document with tags
        doc_tag = DocumentTag(
            document_id="doc-tech-123",
            tag_name="technology",
            tag_type="domain",
            confidence_score=0.9,
            generated_by="system"
        )
        db_session.add(doc_tag)
        db_session.commit()
        
        # Track document interaction
        await profile_manager.track_user_interaction(
            user_id=sample_user_id,
            interaction_type="document",
            interaction_data={
                "document_id": "doc-tech-123",
                "query_related": True
            }
        )
        
        # Get domain expertise
        expertise = await profile_manager.get_domain_expertise(sample_user_id)
        
        # Should detect technology domain from document tags
        assert "technology" in expertise
        assert expertise["technology"] > 0

if __name__ == "__main__":
    pytest.main([__file__])