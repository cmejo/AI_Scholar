"""
Task 7.1 Verification: Build user profile management

This script verifies that the user profile management system meets all requirements:
- Create UserProfileManager for detailed user profiles
- Implement interaction history tracking and analysis
- Add domain expertise detection and scoring
- Write tests for profile accuracy and updates
- Requirements: 8.1, 8.5
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

# Test database setup
DATABASE_URL = "sqlite:///./test_task_7_1_verification.db"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def verify_task_7_1():
    """Verify Task 7.1: Build user profile management."""
    print("🔍 Task 7.1 Verification: User Profile Management")
    print("=" * 60)
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    verification_results = {
        "user_profile_manager_created": False,
        "detailed_user_profiles": False,
        "interaction_history_tracking": False,
        "behavior_analysis": False,
        "domain_expertise_detection": False,
        "profile_updates": False,
        "personalization_weights": False,
        "tests_comprehensive": False
    }
    
    try:
        print("\n1. Verifying UserProfileManager Creation")
        print("-" * 40)
        
        # Test UserProfileManager instantiation
        profile_manager = UserProfileManager(db)
        interaction_tracker = InteractionTracker(db)
        
        print("✅ UserProfileManager successfully created")
        print("✅ InteractionTracker successfully created")
        verification_results["user_profile_manager_created"] = True
        
        print("\n2. Verifying Detailed User Profile Creation")
        print("-" * 40)
        
        user_id = "verification-user-123"
        
        # Create detailed user preferences
        preferences = UserPreferences(
            language="en",
            response_style="detailed",
            domain_focus=["technology", "science", "business"],
            citation_preference="inline",
            reasoning_display=True,
            uncertainty_tolerance=0.6
        )
        
        # Create user profile
        profile = await profile_manager.create_user_profile(
            user_id=user_id,
            preferences=preferences,
            learning_style="visual"
        )
        
        # Verify profile details
        assert profile.user_id == user_id
        assert profile.preferences.language == "en"
        assert profile.preferences.response_style == "detailed"
        assert profile.learning_style == "visual"
        assert isinstance(profile.interaction_history, dict)
        assert isinstance(profile.domain_expertise, dict)
        
        print("✅ Detailed user profile created successfully")
        print(f"   - User ID: {profile.user_id}")
        print(f"   - Preferences: {len(profile.preferences.model_dump())} settings")
        print(f"   - Learning Style: {profile.learning_style}")
        print(f"   - Interaction History: {len(profile.interaction_history)} fields")
        verification_results["detailed_user_profiles"] = True
        
        print("\n3. Verifying Interaction History Tracking")
        print("-" * 40)
        
        # Track various types of interactions
        
        # Track queries
        for i in range(3):
            await interaction_tracker.track_query(
                user_id=user_id,
                query=f"Test query {i+1} about machine learning",
                response_time=2.0 + i * 0.5,
                sources_used=3 + i,
                satisfaction=0.7 + i * 0.1
            )
        
        # Track document access
        for i in range(2):
            await interaction_tracker.track_document_access(
                user_id=user_id,
                document_id=f"doc-{i+1}",
                query_related=True
            )
        
        # Track feedback
        await interaction_tracker.track_feedback(
            user_id=user_id,
            feedback_type="rating",
            rating=4.5,
            message_id="msg-123"
        )
        
        # Verify tracking
        updated_profile = await profile_manager.get_user_profile(user_id)
        history = updated_profile.interaction_history
        
        assert history["total_queries"] == 3
        assert history["total_documents"] == 2
        assert len(history["query_history"]) == 3
        assert len(history["document_interactions"]) == 2
        assert len(history["feedback_history"]) == 1
        
        print("✅ Interaction history tracking verified")
        print(f"   - Queries tracked: {history['total_queries']}")
        print(f"   - Documents tracked: {history['total_documents']}")
        print(f"   - Feedback tracked: {len(history['feedback_history'])}")
        verification_results["interaction_history_tracking"] = True
        
        print("\n4. Verifying Behavior Analysis")
        print("-" * 40)
        
        # Analyze user behavior
        analysis = await profile_manager.analyze_user_behavior(user_id)
        
        # Verify analysis components
        required_analysis_fields = [
            "total_interactions", "engagement_level", "avg_response_time",
            "avg_query_length", "query_complexity", "avg_satisfaction"
        ]
        
        for field in required_analysis_fields:
            assert field in analysis, f"Missing analysis field: {field}"
        
        print("✅ Behavior analysis verified")
        print(f"   - Analysis fields: {len(analysis)}")
        print(f"   - Engagement level: {analysis['engagement_level']}")
        print(f"   - Query complexity: {analysis['query_complexity']}")
        print(f"   - Average satisfaction: {analysis['avg_satisfaction']:.2f}")
        verification_results["behavior_analysis"] = True
        
        print("\n5. Verifying Domain Expertise Detection")
        print("-" * 40)
        
        # Add document tags for domain expertise detection
        domain_tags = [
            ("doc-1", "technology", "domain", 0.9),
            ("doc-1", "machine learning", "topic", 0.85),
            ("doc-2", "science", "domain", 0.8),
            ("doc-2", "research", "topic", 0.75)
        ]
        
        for doc_id, tag_name, tag_type, confidence in domain_tags:
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
        
        # Verify domain expertise detection
        assert isinstance(expertise, dict)
        assert len(expertise) > 0, "Domain expertise should be detected"
        
        print("✅ Domain expertise detection verified")
        print(f"   - Domains detected: {len(expertise)}")
        for domain, score in expertise.items():
            print(f"   - {domain}: {score:.2f}")
        verification_results["domain_expertise_detection"] = True
        
        print("\n6. Verifying Profile Updates")
        print("-" * 40)
        
        # Update user preferences
        new_preferences = UserPreferences(
            language="es",  # Changed
            response_style="concise",  # Changed
            domain_focus=["technology", "business"],  # Changed
            citation_preference="footnote",  # Changed
            reasoning_display=False,  # Changed
            uncertainty_tolerance=0.3  # Changed
        )
        
        updated_profile = await profile_manager.update_user_preferences(
            user_id=user_id,
            preferences=new_preferences
        )
        
        # Verify updates
        assert updated_profile.preferences.language == "es"
        assert updated_profile.preferences.response_style == "concise"
        assert updated_profile.preferences.citation_preference == "footnote"
        assert updated_profile.preferences.reasoning_display == False
        assert updated_profile.preferences.uncertainty_tolerance == 0.3
        
        print("✅ Profile updates verified")
        print(f"   - Language updated: {updated_profile.preferences.language}")
        print(f"   - Response style updated: {updated_profile.preferences.response_style}")
        print(f"   - Citation preference updated: {updated_profile.preferences.citation_preference}")
        verification_results["profile_updates"] = True
        
        print("\n7. Verifying Personalization Weights")
        print("-" * 40)
        
        # Get personalization weights
        weights = await profile_manager.get_personalization_weights(user_id)
        
        # Verify weight structure
        required_weight_fields = [
            "response_style_weight", "citation_weight", "reasoning_weight",
            "uncertainty_tolerance", "domain_weights", "satisfaction_weight",
            "complexity_preference"
        ]
        
        for field in required_weight_fields:
            assert field in weights, f"Missing weight field: {field}"
        
        # Verify weight values are reasonable
        for field, value in weights.items():
            if field != "domain_weights":
                assert 0 <= value <= 1, f"Weight {field} should be between 0 and 1"
        
        print("✅ Personalization weights verified")
        print(f"   - Weight fields: {len(weights)}")
        print(f"   - Response style weight: {weights['response_style_weight']:.2f}")
        print(f"   - Uncertainty tolerance: {weights['uncertainty_tolerance']:.2f}")
        verification_results["personalization_weights"] = True
        
        print("\n8. Verifying Test Coverage")
        print("-" * 40)
        
        # Run the actual test suite to verify comprehensive testing
        import subprocess
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/test_user_profile_service.py", "-v", "--tb=no"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        # Check test results
        if result.returncode == 0:
            test_output = result.stdout
            # Count passed tests
            passed_tests = test_output.count("PASSED")
            failed_tests = test_output.count("FAILED")
            
            print(f"✅ Test suite verification completed")
            print(f"   - Tests passed: {passed_tests}")
            print(f"   - Tests failed: {failed_tests}")
            
            if failed_tests == 0 and passed_tests >= 20:
                verification_results["tests_comprehensive"] = True
                print("✅ Comprehensive test coverage verified")
            else:
                print("⚠️  Some tests failed or insufficient coverage")
        else:
            print("❌ Test suite execution failed")
            print(result.stderr)
        
        print("\n" + "=" * 60)
        print("VERIFICATION SUMMARY")
        print("=" * 60)
        
        total_checks = len(verification_results)
        passed_checks = sum(verification_results.values())
        
        for check, passed in verification_results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status} {check.replace('_', ' ').title()}")
        
        print(f"\nOverall Result: {passed_checks}/{total_checks} checks passed")
        
        if passed_checks == total_checks:
            print("🎉 Task 7.1 FULLY VERIFIED - All requirements met!")
            print("\nRequirements Coverage:")
            print("✅ 8.1 - User profile creation and management")
            print("✅ 8.5 - Personalization based on user interactions")
            return True
        else:
            print("⚠️  Task 7.1 PARTIALLY VERIFIED - Some requirements need attention")
            return False
            
    except Exception as e:
        print(f"❌ Verification failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        db.close()

if __name__ == "__main__":
    success = asyncio.run(verify_task_7_1())
    sys.exit(0 if success else 1)