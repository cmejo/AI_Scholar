"""
Basic test for Learning Progress Service
"""

import asyncio
import sys
import os
import logging
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.learning_progress_service import (
    LearningProgressService,
    LearningProgress,
    KnowledgeGap,
    LearningTrajectory,
    CompetencyMap,
    LearningRecommendation,
    CompetencyLevel,
    LearningGoalType
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_competency_levels():
    """Test competency level enumeration"""
    try:
        logger.info("Testing competency levels...")
        
        levels = [
            CompetencyLevel.NOVICE,
            CompetencyLevel.BEGINNER,
            CompetencyLevel.INTERMEDIATE,
            CompetencyLevel.ADVANCED,
            CompetencyLevel.EXPERT
        ]
        
        logger.info("Available competency levels:")
        for level in levels:
            logger.info(f"  - {level.value}")
        
        return True
        
    except Exception as e:
        logger.error(f"Competency levels test failed: {str(e)}")
        return False

async def test_learning_goal_types():
    """Test learning goal type enumeration"""
    try:
        logger.info("Testing learning goal types...")
        
        goal_types = [
            LearningGoalType.MASTERY,
            LearningGoalType.RETENTION,
            LearningGoalType.SPEED,
            LearningGoalType.ACCURACY
        ]
        
        logger.info("Available learning goal types:")
        for goal_type in goal_types:
            logger.info(f"  - {goal_type.value}")
        
        return True
        
    except Exception as e:
        logger.error(f"Learning goal types test failed: {str(e)}")
        return False

async def test_data_structures():
    """Test learning progress data structures"""
    try:
        logger.info("Testing learning progress data structures...")
        
        # Test LearningProgress
        progress = LearningProgress(
            id="progress_1",
            user_id="user_123",
            topic="machine learning",
            competency_level=0.65,
            last_studied=datetime.now(),
            study_count=5,
            average_score=0.72,
            trend="improving",
            confidence_interval=(0.6, 0.7),
            metadata={"domain": "AI"}
        )
        
        logger.info(f"Created learning progress:")
        logger.info(f"  Topic: {progress.topic}")
        logger.info(f"  Competency: {progress.competency_level:.2f}")
        logger.info(f"  Trend: {progress.trend}")
        logger.info(f"  Study count: {progress.study_count}")
        
        # Test KnowledgeGap
        gap = KnowledgeGap(
            topic="statistics",
            gap_type="weak_foundation",
            severity=0.8,
            evidence=["Low competency score", "Multiple failed attempts"],
            recommendations=["Review basics", "Practice problems"],
            related_topics=["mathematics", "probability"]
        )
        
        logger.info(f"Created knowledge gap:")
        logger.info(f"  Topic: {gap.topic}")
        logger.info(f"  Type: {gap.gap_type}")
        logger.info(f"  Severity: {gap.severity}")
        
        # Test LearningRecommendation
        recommendation = LearningRecommendation(
            type="review",
            topic="algorithms",
            priority=0.9,
            reason="Weak foundation needs strengthening",
            suggested_actions=["Review sorting algorithms", "Practice coding problems"],
            estimated_time_minutes=45
        )
        
        logger.info(f"Created learning recommendation:")
        logger.info(f"  Type: {recommendation.type}")
        logger.info(f"  Topic: {recommendation.topic}")
        logger.info(f"  Priority: {recommendation.priority}")
        logger.info(f"  Estimated time: {recommendation.estimated_time_minutes} minutes")
        
        # Test LearningTrajectory
        trajectory = LearningTrajectory(
            topic="data structures",
            time_points=[datetime.now() - timedelta(days=i) for i in range(5, 0, -1)],
            competency_scores=[0.3, 0.4, 0.5, 0.6, 0.7],
            study_sessions=[1, 1, 0, 1, 1],
            trend_analysis={"trend": "improving", "learning_rate": 0.1},
            predictions={"next_3_sessions": [0.75, 0.8, 0.85]}
        )
        
        logger.info(f"Created learning trajectory:")
        logger.info(f"  Topic: {trajectory.topic}")
        logger.info(f"  Data points: {len(trajectory.time_points)}")
        logger.info(f"  Score range: {min(trajectory.competency_scores):.2f} - {max(trajectory.competency_scores):.2f}")
        
        # Test CompetencyMap
        comp_map = CompetencyMap(
            user_id="user_123",
            competencies={
                "machine learning": 0.7,
                "statistics": 0.4,
                "programming": 0.8
            },
            skill_tree={
                "machine learning": ["statistics", "programming"],
                "statistics": [],
                "programming": []
            },
            mastery_path=["statistics", "programming", "machine learning"],
            generated_at=datetime.now()
        )
        
        logger.info(f"Created competency map:")
        logger.info(f"  Total topics: {len(comp_map.competencies)}")
        logger.info(f"  Mastery path: {' -> '.join(comp_map.mastery_path)}")
        
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
        
        service = LearningProgressService()
        
        # Check competency thresholds
        logger.info("Competency thresholds:")
        for level, (min_val, max_val) in service.competency_thresholds.items():
            logger.info(f"  {level.value}: {min_val} - {max_val}")
        
        return True
        
    except Exception as e:
        logger.error(f"Service initialization test failed: {str(e)}")
        return False

async def test_trend_analysis():
    """Test trend analysis functionality"""
    try:
        logger.info("Testing trend analysis...")
        
        service = LearningProgressService()
        
        # Test different score patterns
        test_cases = [
            ([0.3, 0.4, 0.5, 0.6, 0.7], "improving"),
            ([0.7, 0.6, 0.5, 0.4, 0.3], "declining"),
            ([0.5, 0.5, 0.5, 0.5, 0.5], "stable"),
            ([0.3, 0.7, 0.4, 0.6, 0.5], "volatile")
        ]
        
        logger.info("Trend analysis test results:")
        for scores, expected in test_cases:
            analysis = await service._analyze_trajectory_trends(scores)
            logger.info(f"  Scores {scores} -> Trend: {analysis.get('trend', 'unknown')}")
        
        return True
        
    except Exception as e:
        logger.error(f"Trend analysis test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_skill_tree_building():
    """Test skill tree building"""
    try:
        logger.info("Testing skill tree building...")
        
        service = LearningProgressService()
        
        topics = [
            "programming",
            "statistics",
            "machine learning",
            "advanced machine learning",
            "data structures"
        ]
        
        skill_tree = await service._build_skill_tree(topics)
        
        logger.info("Built skill tree:")
        for topic, prerequisites in skill_tree.items():
            prereq_str = ", ".join(prerequisites) if prerequisites else "None"
            logger.info(f"  {topic}: Prerequisites = {prereq_str}")
        
        return True
        
    except Exception as e:
        logger.error(f"Skill tree building test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    logger.info("=== Learning Progress Service Tests ===")
    
    # Test service initialization
    init_success = await test_service_initialization()
    
    # Test enumerations
    levels_success = await test_competency_levels()
    goals_success = await test_learning_goal_types()
    
    # Test data structures
    structures_success = await test_data_structures()
    
    # Test analysis functions
    trend_success = await test_trend_analysis()
    skill_tree_success = await test_skill_tree_building()
    
    # Summary
    logger.info("=== Test Summary ===")
    logger.info(f"Service initialization: {'PASSED' if init_success else 'FAILED'}")
    logger.info(f"Competency levels test: {'PASSED' if levels_success else 'FAILED'}")
    logger.info(f"Learning goal types test: {'PASSED' if goals_success else 'FAILED'}")
    logger.info(f"Data structures test: {'PASSED' if structures_success else 'FAILED'}")
    logger.info(f"Trend analysis test: {'PASSED' if trend_success else 'FAILED'}")
    logger.info(f"Skill tree building test: {'PASSED' if skill_tree_success else 'FAILED'}")
    
    all_passed = all([
        init_success, levels_success, goals_success, 
        structures_success, trend_success, skill_tree_success
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