"""
Basic test for Spaced Repetition Service
"""

import asyncio
import sys
import os
import logging
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.spaced_repetition_service import (
    SpacedRepetitionService,
    SpacedRepetitionItem,
    ReviewSession,
    ReviewQuality,
    ContentType,
    PerformanceMetrics
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_sr_data_structures():
    """Test spaced repetition data structures"""
    try:
        logger.info("Testing spaced repetition data structures...")
        
        # Test SpacedRepetitionItem creation
        item = SpacedRepetitionItem(
            id="sr_test_1",
            user_id="user_123",
            content_id="quiz_question_1",
            content_type=ContentType.QUIZ_QUESTION,
            difficulty=2.5,
            interval=1,
            repetitions=0,
            ease_factor=2.5,
            metadata={"topic": "machine learning"}
        )
        
        logger.info(f"Created SR item: {item.content_id}")
        logger.info(f"Content type: {item.content_type.value}")
        logger.info(f"Difficulty: {item.difficulty}")
        logger.info(f"Interval: {item.interval} days")
        logger.info(f"Next review: {item.next_review_date}")
        
        # Test ReviewSession creation
        session = ReviewSession(
            id="session_test_1",
            user_id="user_123",
            started_at=datetime.now()
        )
        
        logger.info(f"Created review session: {session.id}")
        logger.info(f"Started at: {session.started_at}")
        
        # Test PerformanceMetrics
        metrics = PerformanceMetrics(
            total_reviews=10,
            correct_reviews=8,
            accuracy_rate=0.8,
            average_ease_factor=2.3,
            retention_rate=0.75,
            streak_count=5
        )
        
        logger.info(f"Performance metrics:")
        logger.info(f"  Accuracy: {metrics.accuracy_rate:.1%}")
        logger.info(f"  Retention: {metrics.retention_rate:.1%}")
        logger.info(f"  Streak: {metrics.streak_count} days")
        
        return True
        
    except Exception as e:
        logger.error(f"Data structure test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_review_qualities():
    """Test review quality enumeration"""
    try:
        logger.info("Testing review qualities...")
        
        qualities = [
            ReviewQuality.BLACKOUT,
            ReviewQuality.INCORRECT,
            ReviewQuality.DIFFICULT,
            ReviewQuality.HESITANT,
            ReviewQuality.EASY,
            ReviewQuality.PERFECT
        ]
        
        logger.info("Available review qualities:")
        for quality in qualities:
            logger.info(f"  {quality.value}: {quality.name}")
        
        return True
        
    except Exception as e:
        logger.error(f"Review qualities test failed: {str(e)}")
        return False

async def test_content_types():
    """Test content type enumeration"""
    try:
        logger.info("Testing content types...")
        
        content_types = [
            ContentType.QUIZ_QUESTION,
            ContentType.CONCEPT,
            ContentType.FACT,
            ContentType.DEFINITION,
            ContentType.FORMULA
        ]
        
        logger.info("Available content types:")
        for ct in content_types:
            logger.info(f"  - {ct.value}")
        
        return True
        
    except Exception as e:
        logger.error(f"Content types test failed: {str(e)}")
        return False

async def test_supermemo_algorithm():
    """Test SuperMemo algorithm calculations"""
    try:
        logger.info("Testing SuperMemo algorithm...")
        
        sr_service = SpacedRepetitionService()
        
        # Test different quality ratings
        test_cases = [
            (2.5, 1, 0, ReviewQuality.PERFECT),
            (2.5, 1, 0, ReviewQuality.EASY),
            (2.5, 1, 0, ReviewQuality.HESITANT),
            (2.5, 1, 0, ReviewQuality.DIFFICULT),
            (2.5, 1, 0, ReviewQuality.INCORRECT),
            (2.5, 1, 0, ReviewQuality.BLACKOUT)
        ]
        
        logger.info("SuperMemo algorithm test results:")
        for ease_factor, interval, repetitions, quality in test_cases:
            new_ease, new_interval, new_reps = sr_service._calculate_supermemo_parameters(
                ease_factor, interval, repetitions, quality
            )
            logger.info(f"  Quality {quality.value}: ease={new_ease:.2f}, interval={new_interval}, reps={new_reps}")
        
        return True
        
    except Exception as e:
        logger.error(f"SuperMemo algorithm test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_service_initialization():
    """Test service initialization"""
    try:
        logger.info("Testing service initialization...")
        
        sr_service = SpacedRepetitionService()
        
        # Check constants
        logger.info(f"Min ease factor: {sr_service.MIN_EASE_FACTOR}")
        logger.info(f"Initial ease factor: {sr_service.INITIAL_EASE_FACTOR}")
        logger.info(f"Min interval: {sr_service.MIN_INTERVAL}")
        logger.info(f"Graduation interval: {sr_service.GRADUATION_INTERVAL}")
        
        return True
        
    except Exception as e:
        logger.error(f"Service initialization test failed: {str(e)}")
        return False

async def main():
    """Run all tests"""
    logger.info("=== Spaced Repetition Service Tests ===")
    
    # Test service initialization
    init_success = await test_service_initialization()
    
    # Test data structures
    structures_success = await test_sr_data_structures()
    
    # Test enumerations
    qualities_success = await test_review_qualities()
    types_success = await test_content_types()
    
    # Test algorithm
    algorithm_success = await test_supermemo_algorithm()
    
    # Summary
    logger.info("=== Test Summary ===")
    logger.info(f"Service initialization: {'PASSED' if init_success else 'FAILED'}")
    logger.info(f"Data structures test: {'PASSED' if structures_success else 'FAILED'}")
    logger.info(f"Review qualities test: {'PASSED' if qualities_success else 'FAILED'}")
    logger.info(f"Content types test: {'PASSED' if types_success else 'FAILED'}")
    logger.info(f"SuperMemo algorithm test: {'PASSED' if algorithm_success else 'FAILED'}")
    
    all_passed = all([
        init_success, structures_success, qualities_success, 
        types_success, algorithm_success
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