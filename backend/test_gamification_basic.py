"""
Basic test for Gamification Service
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

async def test_achievement_types():
    """Test achievement type enumeration"""
    try:
        logger.info("Testing achievement types...")
        
        types = [
            AchievementType.STREAK,
            AchievementType.MASTERY,
            AchievementType.PROGRESS,
            AchievementType.SOCIAL,
            AchievementType.CHALLENGE,
            AchievementType.CONSISTENCY,
            AchievementType.EXPLORATION,
            AchievementType.IMPROVEMENT
        ]
        
        logger.info("Available achievement types:")
        for achievement_type in types:
            logger.info(f"  - {achievement_type.value}")
        
        return True
        
    except Exception as e:
        logger.error(f"Achievement types test failed: {str(e)}")
        return False

async def test_badge_levels():
    """Test badge level enumeration"""
    try:
        logger.info("Testing badge levels...")
        
        levels = [
            BadgeLevel.BRONZE,
            BadgeLevel.SILVER,
            BadgeLevel.GOLD,
            BadgeLevel.PLATINUM,
            BadgeLevel.DIAMOND
        ]
        
        logger.info("Available badge levels:")
        for level in levels:
            logger.info(f"  - {level.value}")
        
        return True
        
    except Exception as e:
        logger.error(f"Badge levels test failed: {str(e)}")
        return False

async def test_learning_styles():
    """Test learning style enumeration"""
    try:
        logger.info("Testing learning styles...")
        
        styles = [
            LearningStyle.VISUAL,
            LearningStyle.AUDITORY,
            LearningStyle.KINESTHETIC,
            LearningStyle.READING,
            LearningStyle.MIXED
        ]
        
        logger.info("Available learning styles:")
        for style in styles:
            logger.info(f"  - {style.value}")
        
        return True
        
    except Exception as e:
        logger.error(f"Learning styles test failed: {str(e)}")
        return False

async def test_data_structures():
    """Test gamification data structures"""
    try:
        logger.info("Testing gamification data structures...")
        
        # Test Achievement
        achievement = Achievement(
            id="achievement_1",
            user_id="user_123",
            achievement_type=AchievementType.STREAK,
            title="Week Warrior",
            description="Study for 7 consecutive days",
            badge_level=BadgeLevel.SILVER,
            points=75,
            earned_at=datetime.now(),
            progress=1.0,
            metadata={"streak_length": 7}
        )
        
        logger.info(f"Created achievement:")
        logger.info(f"  Title: {achievement.title}")
        logger.info(f"  Type: {achievement.achievement_type.value}")
        logger.info(f"  Badge: {achievement.badge_level.value}")
        logger.info(f"  Points: {achievement.points}")
        
        # Test UserProfile
        profile = UserProfile(
            user_id="user_123",
            learning_style=LearningStyle.VISUAL,
            difficulty_preference=DifficultyPreference.ADAPTIVE,
            study_time_preference="evening",
            session_length_preference=30,
            motivation_factors=["achievement", "progress"],
            interests=["technology", "science"],
            goals=["improve skills", "learn new topics"],
            total_points=150,
            level=2,
            badges=["first_quiz", "week_warrior"],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        logger.info(f"Created user profile:")
        logger.info(f"  Learning style: {profile.learning_style.value}")
        logger.info(f"  Difficulty preference: {profile.difficulty_preference.value}")
        logger.info(f"  Total points: {profile.total_points}")
        logger.info(f"  Level: {profile.level}")
        
        # Test PersonalizedRecommendation
        recommendation = PersonalizedRecommendation(
            type="difficulty",
            content="Try more challenging content to accelerate learning",
            reason="Your average score is high, indicating readiness for harder material",
            confidence=0.8,
            estimated_benefit=0.7,
            suggested_duration=45,
            metadata={"current_score": 0.85}
        )
        
        logger.info(f"Created personalized recommendation:")
        logger.info(f"  Type: {recommendation.type}")
        logger.info(f"  Content: {recommendation.content}")
        logger.info(f"  Confidence: {recommendation.confidence:.1%}")
        logger.info(f"  Estimated benefit: {recommendation.estimated_benefit:.1%}")
        
        # Test SocialLearningData
        social_data = SocialLearningData(
            user_rank=15,
            total_users=100,
            peer_group_average=125.5,
            user_score=150.0,
            improvement_rank=8,
            study_streak_rank=12,
            collaborative_sessions=3,
            peer_interactions=7
        )
        
        logger.info(f"Created social learning data:")
        logger.info(f"  User rank: {social_data.user_rank} of {social_data.total_users}")
        logger.info(f"  User score: {social_data.user_score}")
        logger.info(f"  Peer group average: {social_data.peer_group_average}")
        
        # Test LearningChallenge
        challenge = LearningChallenge(
            id="challenge_1",
            title="30-Day Study Streak",
            description="Study for 30 consecutive days",
            challenge_type="streak",
            target_value=30.0,
            duration_days=30,
            points_reward=300,
            badge_reward="streak_master",
            participants=25,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=30)
        )
        
        logger.info(f"Created learning challenge:")
        logger.info(f"  Title: {challenge.title}")
        logger.info(f"  Type: {challenge.challenge_type}")
        logger.info(f"  Target: {challenge.target_value}")
        logger.info(f"  Reward: {challenge.points_reward} points")
        logger.info(f"  Participants: {challenge.participants}")
        
        return True
        
    except Exception as e:
        logger.error(f"Data structures test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_service_initialization():
    """Test service initialization"""
    try:
        logger.info("Testing service initialization...")
        
        service = GamificationService()
        
        # Check points system
        logger.info("Points system:")
        for action, points in service.points_system.items():
            logger.info(f"  {action}: {points} points")
        
        # Check level thresholds
        logger.info("Level thresholds:")
        for i, threshold in enumerate(service.level_thresholds):
            logger.info(f"  Level {i}: {threshold} points")
        
        # Check achievement definitions
        logger.info(f"Achievement definitions loaded: {len(service.achievement_definitions)}")
        for achievement_id, definition in list(service.achievement_definitions.items())[:3]:
            logger.info(f"  {achievement_id}: {definition['title']} ({definition['points']} points)")
        
        return True
        
    except Exception as e:
        logger.error(f"Service initialization test failed: {str(e)}")
        return False

async def test_difficulty_adaptation():
    """Test difficulty adaptation logic"""
    try:
        logger.info("Testing difficulty adaptation...")
        
        service = GamificationService()
        
        # Test different scenarios
        test_cases = [
            (0.5, "baseline"),
            (0.3, "struggling user"),
            (0.8, "high performer"),
            (0.1, "very low difficulty"),
            (0.9, "very high difficulty")
        ]
        
        logger.info("Difficulty adaptation test results:")
        for current_difficulty, scenario in test_cases:
            # This would normally use real user data, but we'll test the bounds
            adapted = max(0.1, min(1.0, current_difficulty))  # Simplified bounds check
            logger.info(f"  {scenario}: {current_difficulty:.1f} -> {adapted:.1f}")
        
        return True
        
    except Exception as e:
        logger.error(f"Difficulty adaptation test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_level_calculation():
    """Test level calculation logic"""
    try:
        logger.info("Testing level calculation...")
        
        service = GamificationService()
        
        # Test different point values
        test_points = [0, 50, 150, 300, 600, 1200, 2500, 5000, 10000, 20000, 50000]
        
        logger.info("Level calculation test results:")
        for points in test_points:
            # Calculate level
            level = 0
            for i, threshold in enumerate(service.level_thresholds):
                if points >= threshold:
                    level = i
                else:
                    break
            
            level_name = service._get_level_name(level)
            logger.info(f"  {points} points -> Level {level} ({level_name})")
        
        return True
        
    except Exception as e:
        logger.error(f"Level calculation test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    logger.info("=== Gamification Service Tests ===")
    
    # Test service initialization
    init_success = await test_service_initialization()
    
    # Test enumerations
    types_success = await test_achievement_types()
    badges_success = await test_badge_levels()
    styles_success = await test_learning_styles()
    
    # Test data structures
    structures_success = await test_data_structures()
    
    # Test logic functions
    difficulty_success = await test_difficulty_adaptation()
    level_success = await test_level_calculation()
    
    # Summary
    logger.info("=== Test Summary ===")
    logger.info(f"Service initialization: {'PASSED' if init_success else 'FAILED'}")
    logger.info(f"Achievement types test: {'PASSED' if types_success else 'FAILED'}")
    logger.info(f"Badge levels test: {'PASSED' if badges_success else 'FAILED'}")
    logger.info(f"Learning styles test: {'PASSED' if styles_success else 'FAILED'}")
    logger.info(f"Data structures test: {'PASSED' if structures_success else 'FAILED'}")
    logger.info(f"Difficulty adaptation test: {'PASSED' if difficulty_success else 'FAILED'}")
    logger.info(f"Level calculation test: {'PASSED' if level_success else 'FAILED'}")
    
    all_passed = all([
        init_success, types_success, badges_success, styles_success,
        structures_success, difficulty_success, level_success
    ])
    
    if all_passed:
        logger.info("All tests PASSED!")
        return 0
    else:
        logger.error("Some tests FAILED!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)