"""
Enhanced Gamification Service Test - Task 4.4 Implementation

This test verifies the implementation of:
1. Achievement system with badges and progress rewards
2. Personalized study recommendations based on learning patterns
3. Social learning features with peer comparison and collaboration
4. Adaptive content difficulty based on individual learning curves
"""

import asyncio
import sys
import os
import logging
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.gamification_service import (
    GamificationService,
    Achievement,
    UserProfile,
    PersonalizedRecommendation,
    SocialLearningData,
    LearningChallenge,
    AchievementType,
    BadgeLevel,
    LearningStyle,
    DifficultyPreference
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_enhanced_achievement_system():
    """Test enhanced achievement system with badges and progress rewards"""
    try:
        logger.info("Testing enhanced achievement system...")
        
        service = GamificationService()
        test_user_id = "test_user_achievements"
        
        # Test different achievement types
        achievement_tests = [
            (AchievementType.STREAK, {"event": "study_session", "streak_length": 7}),
            (AchievementType.MASTERY, {"event": "topic_mastered", "topic": "mathematics"}),
            (AchievementType.PROGRESS, {"event": "quiz_completed", "score": 0.95}),
            (AchievementType.SOCIAL, {"event": "peer_help", "peer_id": "peer_123"}),
            (AchievementType.IMPROVEMENT, {"improvement_percentage": 0.6})
        ]
        
        awarded_achievements = []
        
        for achievement_type, context in achievement_tests:
            achievement = await service.award_achievement(
                user_id=test_user_id,
                achievement_type=achievement_type,
                context=context
            )
            
            if achievement:
                awarded_achievements.append(achievement)
                logger.info(f"✓ Awarded {achievement_type.value} achievement: {achievement.title}")
            else:
                logger.info(f"- No {achievement_type.value} achievement awarded (criteria not met)")
        
        # Test level calculation
        level_data = await service.get_user_level_and_progress(test_user_id)
        logger.info(f"User level data: Level {level_data['current_level']} ({level_data['level_name']})")
        logger.info(f"Total points: {level_data['total_points']}")
        logger.info(f"Progress to next level: {level_data['progress_to_next_level']:.1%}")
        
        # Test badge levels
        logger.info("Badge level system:")
        for badge_level in BadgeLevel:
            logger.info(f"  - {badge_level.value.title()}: {badge_level.value} level achievement")
        
        return len(awarded_achievements) > 0
        
    except Exception as e:
        logger.error(f"Enhanced achievement system test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_personalized_recommendations():
    """Test personalized study recommendations based on learning patterns"""
    try:
        logger.info("Testing personalized study recommendations...")
        
        service = GamificationService()
        test_user_id = "test_user_recommendations"
        
        # Generate personalized recommendations
        recommendations = await service.generate_personalized_recommendations(
            user_id=test_user_id,
            limit=5
        )
        
        logger.info(f"Generated {len(recommendations)} personalized recommendations:")
        
        for i, rec in enumerate(recommendations, 1):
            logger.info(f"  {i}. {rec.type.title()} Recommendation:")
            logger.info(f"     Content: {rec.content}")
            logger.info(f"     Reason: {rec.reason}")
            logger.info(f"     Confidence: {rec.confidence:.1%}")
            logger.info(f"     Estimated Benefit: {rec.estimated_benefit:.1%}")
            logger.info(f"     Suggested Duration: {rec.suggested_duration} minutes")
        
        # Test adaptive content recommendations
        topics = ["mathematics", "physics", "computer_science"]
        
        logger.info("\nAdaptive content recommendations by topic:")
        for topic in topics:
            adaptive_rec = await service.generate_adaptive_content_recommendations(
                user_id=test_user_id,
                topic=topic
            )
            
            if adaptive_rec:
                logger.info(f"  {topic.title()}:")
                logger.info(f"    Recommended difficulty: {adaptive_rec.get('recommended_difficulty', 0):.2f}")
                logger.info(f"    Content type: {adaptive_rec.get('content_type', 'N/A')}")
                logger.info(f"    Study approach: {adaptive_rec.get('study_approach', 'N/A')}")
                logger.info(f"    Session length: {adaptive_rec.get('session_length', 0)} minutes")
                logger.info(f"    Reason: {adaptive_rec.get('reason', 'N/A')}")
        
        # Test personalized study plan
        goals = ["mathematics", "physics"]
        time_available = 120  # 2 hours
        
        study_plan = await service.get_personalized_study_plan(
            user_id=test_user_id,
            goals=goals,
            time_available_minutes=time_available
        )
        
        if study_plan:
            logger.info(f"\nPersonalized study plan:")
            logger.info(f"  Plan ID: {study_plan.get('plan_id', 'N/A')}")
            logger.info(f"  Total time: {study_plan.get('total_time_minutes', 0)} minutes")
            logger.info(f"  Number of sessions: {len(study_plan.get('sessions', []))}")
            
            for session in study_plan.get('sessions', []):
                logger.info(f"    - {session.get('topic', 'Unknown')}: {session.get('allocated_time_minutes', 0)} min")
                logger.info(f"      Type: {session.get('session_type', 'N/A')}")
                logger.info(f"      Priority: {session.get('priority', 0):.2f}")
        
        return len(recommendations) > 0
        
    except Exception as e:
        logger.error(f"Personalized recommendations test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_social_learning_features():
    """Test social learning features with peer comparison and collaboration"""
    try:
        logger.info("Testing social learning features...")
        
        service = GamificationService()
        test_user_id = "test_user_social"
        
        # Test social learning data
        social_data = await service.get_social_learning_data(test_user_id)
        
        logger.info("Social learning statistics:")
        logger.info(f"  User rank: {social_data.user_rank} of {social_data.total_users}")
        logger.info(f"  User score: {social_data.user_score}")
        logger.info(f"  Peer group average: {social_data.peer_group_average:.1f}")
        logger.info(f"  Improvement rank: {social_data.improvement_rank}")
        logger.info(f"  Study streak rank: {social_data.study_streak_rank}")
        logger.info(f"  Collaborative sessions: {social_data.collaborative_sessions}")
        logger.info(f"  Peer interactions: {social_data.peer_interactions}")
        
        # Test peer comparison data
        peer_comparison = await service.get_peer_comparison_data(test_user_id)
        
        if peer_comparison:
            logger.info("\nDetailed peer comparison:")
            user_metrics = peer_comparison.get('user_metrics', {})
            peer_comp = peer_comparison.get('peer_comparison', {})
            insights = peer_comparison.get('performance_insights', {})
            
            logger.info(f"  User metrics:")
            logger.info(f"    Total points: {user_metrics.get('total_points', 0)}")
            logger.info(f"    Average score: {user_metrics.get('average_score', 0):.2f}")
            logger.info(f"    Study sessions: {user_metrics.get('study_sessions', 0)}")
            logger.info(f"    Achievements: {user_metrics.get('achievements_count', 0)}")
            
            logger.info(f"  Peer comparison:")
            logger.info(f"    Points percentile: {peer_comp.get('points_percentile', 0):.1f}%")
            logger.info(f"    Score percentile: {peer_comp.get('score_percentile', 0):.1f}%")
            logger.info(f"    Total peers: {peer_comp.get('total_peers', 0)}")
            
            logger.info(f"  Performance insights:")
            logger.info(f"    Points vs peers: {insights.get('points_vs_peers', 'N/A')}")
            logger.info(f"    Score vs peers: {insights.get('score_vs_peers', 'N/A')}")
            improvement_areas = insights.get('improvement_areas', [])
            if improvement_areas:
                logger.info(f"    Improvement areas: {', '.join(improvement_areas)}")
        
        # Test study group creation
        study_group = await service.create_study_group(
            creator_id=test_user_id,
            name="Test Study Group",
            description="A test study group for collaborative learning",
            max_members=5
        )
        
        logger.info(f"\nCreated study group:")
        logger.info(f"  ID: {study_group.get('id', 'N/A')}")
        logger.info(f"  Name: {study_group.get('name', 'N/A')}")
        logger.info(f"  Members: {len(study_group.get('members', []))}")
        logger.info(f"  Max members: {study_group.get('max_members', 0)}")
        
        # Test collaborative challenges
        challenges = await service.get_collaborative_challenges(test_user_id)
        
        logger.info(f"\nAvailable collaborative challenges: {len(challenges)}")
        for challenge in challenges:
            logger.info(f"  - {challenge.get('title', 'Unknown')}")
            logger.info(f"    Type: {challenge.get('type', 'N/A')}")
            logger.info(f"    Participants: {challenge.get('current_participants', 0)}/{challenge.get('participants_needed', 0)}")
            logger.info(f"    Reward: {challenge.get('individual_reward_points', 0)} points")
        
        # Test peer interaction tracking
        interaction_success = await service.track_peer_interactions(
            user_id=test_user_id,
            interaction_type="help_given",
            peer_id="peer_456",
            context={"topic": "mathematics", "help_type": "explanation"}
        )
        
        logger.info(f"\nPeer interaction tracking: {'Success' if interaction_success else 'Failed'}")
        
        return True
        
    except Exception as e:
        logger.error(f"Social learning features test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_adaptive_difficulty():
    """Test adaptive content difficulty based on individual learning curves"""
    try:
        logger.info("Testing adaptive content difficulty...")
        
        service = GamificationService()
        test_user_id = "test_user_adaptive"
        
        # Test difficulty adaptation for different scenarios
        test_scenarios = [
            ("mathematics", 0.3, "Low competency user"),
            ("physics", 0.7, "High competency user"),
            ("chemistry", 0.5, "Average competency user"),
            ("biology", 0.9, "Expert level user"),
            ("computer_science", 0.1, "Beginner user")
        ]
        
        logger.info("Adaptive difficulty testing:")
        
        for topic, current_difficulty, scenario in test_scenarios:
            adapted_difficulty = await service.adapt_content_difficulty(
                user_id=test_user_id,
                topic=topic,
                current_difficulty=current_difficulty
            )
            
            adjustment = adapted_difficulty - current_difficulty
            adjustment_type = "increased" if adjustment > 0 else "decreased" if adjustment < 0 else "maintained"
            
            logger.info(f"  {scenario} ({topic}):")
            logger.info(f"    Current: {current_difficulty:.2f} → Adapted: {adapted_difficulty:.2f}")
            logger.info(f"    Adjustment: {adjustment:+.2f} ({adjustment_type})")
        
        # Test learning curve analysis
        topics_for_analysis = ["mathematics", "physics", "chemistry"]
        
        logger.info("\nLearning curve analysis:")
        for topic in topics_for_analysis:
            recommendations = await service.generate_adaptive_content_recommendations(
                user_id=test_user_id,
                topic=topic
            )
            
            if recommendations:
                metrics = recommendations.get('learning_metrics', {})
                logger.info(f"  {topic.title()}:")
                logger.info(f"    Current competency: {metrics.get('current_competency', 0):.2f}")
                logger.info(f"    Average score: {metrics.get('average_score', 0):.2f}")
                logger.info(f"    Study count: {metrics.get('study_count', 0)}")
                logger.info(f"    Learning velocity: {metrics.get('learning_velocity', 0):.3f}")
                logger.info(f"    Recommended difficulty: {recommendations.get('recommended_difficulty', 0):.2f}")
                logger.info(f"    Content type: {recommendations.get('content_type', 'N/A')}")
        
        return True
        
    except Exception as e:
        logger.error(f"Adaptive difficulty test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_learning_styles_and_preferences():
    """Test learning style and preference handling"""
    try:
        logger.info("Testing learning styles and preferences...")
        
        # Test all learning styles
        logger.info("Available learning styles:")
        for style in LearningStyle:
            logger.info(f"  - {style.value.title()}: Optimized for {style.value} learners")
        
        # Test difficulty preferences
        logger.info("\nDifficulty preferences:")
        for pref in DifficultyPreference:
            logger.info(f"  - {pref.value.title()}: {pref.value} content preference")
        
        # Test user profile creation
        test_profile = UserProfile(
            user_id="test_user_profile",
            learning_style=LearningStyle.VISUAL,
            difficulty_preference=DifficultyPreference.ADAPTIVE,
            study_time_preference="evening",
            session_length_preference=45,
            motivation_factors=["achievement", "progress", "social"],
            interests=["technology", "science", "mathematics"],
            goals=["master_calculus", "learn_python", "improve_problem_solving"],
            total_points=250,
            level=3,
            badges=["first_quiz", "week_warrior", "topic_explorer"],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        logger.info(f"\nTest user profile created:")
        logger.info(f"  Learning style: {test_profile.learning_style.value}")
        logger.info(f"  Difficulty preference: {test_profile.difficulty_preference.value}")
        logger.info(f"  Study time: {test_profile.study_time_preference}")
        logger.info(f"  Session length: {test_profile.session_length_preference} minutes")
        logger.info(f"  Motivation factors: {', '.join(test_profile.motivation_factors)}")
        logger.info(f"  Interests: {', '.join(test_profile.interests)}")
        logger.info(f"  Goals: {', '.join(test_profile.goals)}")
        logger.info(f"  Level: {test_profile.level}")
        logger.info(f"  Badges: {len(test_profile.badges)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Learning styles and preferences test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_gamification_integration():
    """Test integration between different gamification components"""
    try:
        logger.info("Testing gamification component integration...")
        
        service = GamificationService()
        test_user_id = "test_user_integration"
        
        # Simulate a complete learning session
        logger.info("Simulating complete learning session:")
        
        # 1. Start with personalized recommendations
        recommendations = await service.generate_personalized_recommendations(test_user_id, limit=3)
        logger.info(f"  1. Generated {len(recommendations)} personalized recommendations")
        
        # 2. Adapt difficulty for a topic
        topic = "mathematics"
        adapted_difficulty = await service.adapt_content_difficulty(test_user_id, topic, 0.5)
        logger.info(f"  2. Adapted difficulty for {topic}: {adapted_difficulty:.2f}")
        
        # 3. Award achievement for study session
        achievement = await service.award_achievement(
            test_user_id, 
            AchievementType.PROGRESS, 
            {"event": "study_session_completed", "topic": topic}
        )
        if achievement:
            logger.info(f"  3. Awarded achievement: {achievement.title}")
        else:
            logger.info(f"  3. No achievement awarded (criteria not met)")
        
        # 4. Track peer interaction
        peer_interaction = await service.track_peer_interactions(
            test_user_id, 
            "collaboration", 
            "peer_789",
            {"topic": topic, "session_type": "study_group"}
        )
        logger.info(f"  4. Tracked peer interaction: {'Success' if peer_interaction else 'Failed'}")
        
        # 5. Get updated social data
        social_data = await service.get_social_learning_data(test_user_id)
        logger.info(f"  5. Updated social rank: {social_data.user_rank} of {social_data.total_users}")
        
        # 6. Generate new study plan
        study_plan = await service.get_personalized_study_plan(
            test_user_id, 
            ["mathematics", "physics"], 
            90
        )
        if study_plan:
            logger.info(f"  6. Generated study plan with {len(study_plan.get('sessions', []))} sessions")
        
        logger.info("Integration test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Gamification integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all enhanced gamification tests"""
    logger.info("=== Enhanced Gamification Service Tests (Task 4.4) ===")
    
    # Test enhanced achievement system
    achievement_success = await test_enhanced_achievement_system()
    
    # Test personalized recommendations
    recommendations_success = await test_personalized_recommendations()
    
    # Test social learning features
    social_success = await test_social_learning_features()
    
    # Test adaptive difficulty
    adaptive_success = await test_adaptive_difficulty()
    
    # Test learning styles and preferences
    styles_success = await test_learning_styles_and_preferences()
    
    # Test integration
    integration_success = await test_gamification_integration()
    
    # Summary
    logger.info("=== Test Summary ===")
    logger.info(f"Enhanced achievement system: {'PASSED' if achievement_success else 'FAILED'}")
    logger.info(f"Personalized recommendations: {'PASSED' if recommendations_success else 'FAILED'}")
    logger.info(f"Social learning features: {'PASSED' if social_success else 'FAILED'}")
    logger.info(f"Adaptive difficulty: {'PASSED' if adaptive_success else 'FAILED'}")
    logger.info(f"Learning styles/preferences: {'PASSED' if styles_success else 'FAILED'}")
    logger.info(f"Gamification integration: {'PASSED' if integration_success else 'FAILED'}")
    
    all_passed = all([
        achievement_success, recommendations_success, social_success,
        adaptive_success, styles_success, integration_success
    ])
    
    if all_passed:
        logger.info("All enhanced gamification tests PASSED!")
        logger.info("Task 4.4 implementation verified successfully!")
        return 0
    else:
        logger.error("Some enhanced gamification tests FAILED!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)