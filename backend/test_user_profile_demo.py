"""
Demo script for User Profile Management Service

This script demonstrates the functionality of the UserProfileManager
including profile creation, interaction tracking, behavior analysis,
and domain expertise detection.
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.database import Base, DocumentTag
from services.user_profile_service import UserProfileManager, InteractionTracker
from models.schemas import UserPreferences

# Database setup
DATABASE_URL = "sqlite:///./demo_user_profile.db"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def demo_user_profile_management():
    """Demonstrate user profile management functionality."""
    print("🚀 User Profile Management Demo")
    print("=" * 50)
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        # Initialize services
        profile_manager = UserProfileManager(db)
        interaction_tracker = InteractionTracker(db)
        
        # Demo user
        user_id = "demo-user-123"
        
        print("\n1. Creating User Profile")
        print("-" * 30)
        
        # Create user preferences
        preferences = UserPreferences(
            language="en",
            response_style="detailed",
            domain_focus=["technology", "science"],
            citation_preference="inline",
            reasoning_display=True,
            uncertainty_tolerance=0.7
        )
        
        # Create user profile
        profile = await profile_manager.create_user_profile(
            user_id=user_id,
            preferences=preferences,
            learning_style="visual"
        )
        
        print(f"✅ Created profile for user: {profile.user_id}")
        print(f"   Language: {profile.preferences.language}")
        print(f"   Response Style: {profile.preferences.response_style}")
        print(f"   Learning Style: {profile.learning_style}")
        print(f"   Domain Focus: {profile.preferences.domain_focus}")
        
        print("\n2. Tracking User Interactions")
        print("-" * 30)
        
        # Track multiple query interactions
        queries = [
            "What is machine learning and how does it work?",
            "Explain neural networks in detail",
            "How do I implement a CNN in Python?",
            "What are the latest advances in computer vision?",
            "Can you show me examples of deep learning applications?"
        ]
        
        for i, query in enumerate(queries):
            await interaction_tracker.track_query(
                user_id=user_id,
                query=query,
                response_time=2.0 + i * 0.3,
                sources_used=3 + i,
                satisfaction=0.7 + i * 0.05
            )
            print(f"   📝 Tracked query {i+1}: '{query[:50]}...'")
        
        # Track document interactions
        doc_ids = ["doc-ml-101", "doc-neural-nets", "doc-cv-guide"]
        for doc_id in doc_ids:
            await interaction_tracker.track_document_access(
                user_id=user_id,
                document_id=doc_id,
                query_related=True
            )
            print(f"   📄 Tracked document access: {doc_id}")
        
        # Track feedback
        await interaction_tracker.track_feedback(
            user_id=user_id,
            feedback_type="rating",
            rating=4.5,
            message_id="msg-123"
        )
        print(f"   👍 Tracked feedback: rating 4.5/5")
        
        print("\n3. Analyzing User Behavior")
        print("-" * 30)
        
        # Analyze user behavior
        analysis = await profile_manager.analyze_user_behavior(user_id)
        
        print(f"   📊 Total Interactions: {analysis.get('total_interactions', 0)}")
        print(f"   📈 Engagement Level: {analysis.get('engagement_level', 'unknown')}")
        print(f"   ⏱️  Average Response Time: {analysis.get('avg_response_time', 0):.2f}s")
        print(f"   📏 Average Query Length: {analysis.get('avg_query_length', 0):.0f} chars")
        print(f"   🎯 Query Complexity: {analysis.get('query_complexity', 'unknown')}")
        print(f"   😊 Average Satisfaction: {analysis.get('avg_satisfaction', 0):.2f}")
        print(f"   🎨 Inferred Learning Style: {analysis.get('inferred_learning_style', 'unknown')}")
        
        print("\n4. Domain Expertise Detection")
        print("-" * 30)
        
        # Add some document tags to simulate domain expertise detection
        tech_tags = [
            ("doc-ml-101", "technology", "domain", 0.9),
            ("doc-ml-101", "machine learning", "topic", 0.95),
            ("doc-neural-nets", "technology", "domain", 0.85),
            ("doc-neural-nets", "artificial intelligence", "topic", 0.9),
            ("doc-cv-guide", "technology", "domain", 0.8),
            ("doc-cv-guide", "computer vision", "topic", 0.92)
        ]
        
        for doc_id, tag_name, tag_type, confidence in tech_tags:
            tag = DocumentTag(
                document_id=doc_id,
                tag_name=tag_name,
                tag_type=tag_type,
                confidence_score=confidence,
                generated_by="system"
            )
            db.add(tag)
        db.commit()
        
        # Get domain expertise
        expertise = await profile_manager.get_domain_expertise(user_id)
        
        print("   🧠 Detected Domain Expertise:")
        for domain, score in expertise.items():
            print(f"      {domain}: {score:.2f}")
        
        print("\n5. Personalization Weights")
        print("-" * 30)
        
        # Get personalization weights
        weights = await profile_manager.get_personalization_weights(user_id)
        
        print("   ⚖️  Personalization Weights:")
        for weight_type, value in weights.items():
            if weight_type == "domain_weights":
                print(f"      {weight_type}: {dict(value) if value else 'None'}")
            else:
                print(f"      {weight_type}: {value:.2f}")
        
        print("\n6. Profile Updates")
        print("-" * 30)
        
        # Update preferences
        new_preferences = UserPreferences(
            language="en",
            response_style="concise",  # Changed from detailed
            domain_focus=["technology", "science", "business"],  # Added business
            citation_preference="footnote",  # Changed from inline
            reasoning_display=False,  # Changed from True
            uncertainty_tolerance=0.4  # Changed from 0.7
        )
        
        updated_profile = await profile_manager.update_user_preferences(
            user_id=user_id,
            preferences=new_preferences
        )
        
        print("   ✏️  Updated preferences:")
        print(f"      Response Style: {updated_profile.preferences.response_style}")
        print(f"      Domain Focus: {updated_profile.preferences.domain_focus}")
        print(f"      Citation Preference: {updated_profile.preferences.citation_preference}")
        print(f"      Reasoning Display: {updated_profile.preferences.reasoning_display}")
        print(f"      Uncertainty Tolerance: {updated_profile.preferences.uncertainty_tolerance}")
        
        print("\n7. Final Profile Summary")
        print("-" * 30)
        
        final_profile = await profile_manager.get_user_profile(user_id)
        history = final_profile.interaction_history
        
        print(f"   👤 User ID: {final_profile.user_id}")
        print(f"   📅 Created: {final_profile.created_at}")
        print(f"   🔄 Last Updated: {final_profile.updated_at}")
        print(f"   🎯 Total Queries: {history.get('total_queries', 0)}")
        print(f"   📄 Total Documents: {history.get('total_documents', 0)}")
        print(f"   💬 Feedback Count: {len(history.get('feedback_history', []))}")
        print(f"   🧠 Domain Expertise Areas: {len(final_profile.domain_expertise)}")
        
        print("\n✅ Demo completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during demo: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(demo_user_profile_management())