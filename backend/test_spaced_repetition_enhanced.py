"""
Enhanced test for Spaced Repetition Service with advanced features
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

async def test_enhanced_optimization():
    """Test enhanced optimization features"""
    try:
        logger.info("Testing enhanced optimization features...")
        
        sr_service = SpacedRepetitionService()
        user_id = "test_user_enhanced"
        
        # Create test items with different performance patterns
        items = []
        
        # High performer item
        high_performer = await sr_service.add_item_to_review(
            user_id=user_id,
            content_id="high_performer_concept",
            content_type=ContentType.CONCEPT,
            initial_difficulty=2.5,
            metadata={"topic": "easy_concept"}
        )
        
        # Simulate excellent performance history
        for i in range(5):
            high_performer = await sr_service.record_review(
                item_id=high_performer.id,
                user_id=user_id,
                quality=ReviewQuality.PERFECT,
                response_time_seconds=10
            )
        
        items.append(high_performer)
        
        # Struggling item
        struggling_item = await sr_service.add_item_to_review(
            user_id=user_id,
            content_id="struggling_formula",
            content_type=ContentType.FORMULA,
            initial_difficulty=2.5,
            metadata={"topic": "difficult_formula"}
        )
        
        # Simulate poor performance history
        for i in range(5):
            struggling_item = await sr_service.record_review(
                item_id=struggling_item.id,
                user_id=user_id,
                quality=ReviewQuality.DIFFICULT if i % 2 == 0 else ReviewQuality.INCORRECT,
                response_time_seconds=60
            )
        
        items.append(struggling_item)
        
        # Test optimization
        optimization_result = await sr_service.optimize_review_timing(user_id)
        
        logger.info("Optimization results:")
        logger.info(f"  Total items: {optimization_result['total_items']}")
        logger.info(f"  Adjustments made: {optimization_result['adjustments_made']}")
        logger.info(f"  High performers: {optimization_result['performance_analysis']['high_performers']}")
        logger.info(f"  Struggling items: {optimization_result['performance_analysis']['struggling_items']}")
        logger.info(f"  Ease factor increases: {optimization_result['timing_adjustments']['ease_factor_increases']}")
        logger.info(f"  Ease factor decreases: {optimization_result['timing_adjustments']['ease_factor_decreases']}")
        
        for recommendation in optimization_result['recommendations']:
            logger.info(f"  Recommendation: {recommendation}")
        
        return optimization_result['adjustments_made'] > 0
        
    except Exception as e:
        logger.error(f"Enhanced optimization test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_optimal_session_timing():
    """Test optimal session timing calculations"""
    try:
        logger.info("Testing optimal session timing...")
        
        sr_service = SpacedRepetitionService()
        user_id = "test_user_timing"
        
        # Create some review sessions with different patterns
        sessions = []
        
        # Morning session with good performance
        morning_session = await sr_service.start_review_session(user_id)
        # Simulate morning time (9 AM)
        morning_session.started_at = datetime.now().replace(hour=9, minute=0)
        
        await asyncio.sleep(0.1)  # Simulate session duration
        
        morning_session = await sr_service.end_review_session(
            session_id=morning_session.id,
            user_id=user_id,
            items_reviewed=["item1", "item2", "item3"],
            performance_scores=[4.0, 5.0, 4.0]
        )
        sessions.append(morning_session)
        
        # Get optimal timing recommendations
        timing_result = await sr_service.get_optimal_session_timing(user_id)
        
        logger.info("Optimal session timing results:")
        logger.info(f"  Recommended session length: {timing_result['recommended_session_length']} minutes")
        logger.info(f"  Recommended items per session: {timing_result['recommended_items_per_session']}")
        logger.info(f"  Optimal time of day: {timing_result['optimal_time_of_day']}")
        logger.info(f"  Confidence: {timing_result['confidence']}")
        logger.info(f"  Reasoning: {timing_result['reasoning']}")
        
        if 'session_analysis' in timing_result:
            analysis = timing_result['session_analysis']
            logger.info(f"  Sessions analyzed: {analysis['sessions_analyzed']}")
            logger.info(f"  Average performance: {analysis['average_performance']:.2f}")
        
        return 'recommended_session_length' in timing_result
        
    except Exception as e:
        logger.error(f"Optimal session timing test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_advanced_retention_analytics():
    """Test advanced retention analytics"""
    try:
        logger.info("Testing advanced retention analytics...")
        
        sr_service = SpacedRepetitionService()
        user_id = "test_user_analytics"
        
        # Create items of different content types
        content_types = [ContentType.CONCEPT, ContentType.FACT, ContentType.FORMULA]
        
        for i, ct in enumerate(content_types):
            item = await sr_service.add_item_to_review(
                user_id=user_id,
                content_id=f"test_item_{ct.value}_{i}",
                content_type=ct,
                initial_difficulty=2.5,
                metadata={"topic": f"test_topic_{i}"}
            )
            
            # Simulate different performance patterns for each content type
            for j in range(3):
                quality = ReviewQuality.PERFECT if ct == ContentType.CONCEPT else \
                         ReviewQuality.EASY if ct == ContentType.FACT else \
                         ReviewQuality.DIFFICULT
                
                await sr_service.record_review(
                    item_id=item.id,
                    user_id=user_id,
                    quality=quality,
                    response_time_seconds=20 + j * 10
                )
        
        # Get advanced analytics
        analytics_result = await sr_service.get_advanced_retention_analytics(user_id)
        
        logger.info("Advanced retention analytics results:")
        
        if 'retention_by_content_type' in analytics_result:
            logger.info("  Retention by content type:")
            for ct, data in analytics_result['retention_by_content_type'].items():
                logger.info(f"    {ct}: {data['retention_rate']:.2%} retention, {data['item_count']} items")
        
        if 'difficulty_progression' in analytics_result:
            progression = analytics_result['difficulty_progression']
            logger.info(f"  Difficulty progression: {progression.get('trend', 'unknown')}")
            logger.info(f"  Latest average quality: {progression.get('latest_average', 0):.2f}")
        
        if 'predicted_retention' in analytics_result:
            logger.info("  Predicted retention:")
            for period, data in analytics_result['predicted_retention'].items():
                logger.info(f"    {period}: {data['items_due']} items due, {data['predicted_retention_rate']:.2%} retention")
        
        if 'recommendations' in analytics_result:
            logger.info("  Recommendations:")
            for rec in analytics_result['recommendations']:
                logger.info(f"    - {rec}")
        
        return 'retention_by_content_type' in analytics_result
        
    except Exception as e:
        logger.error(f"Advanced retention analytics test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_enhanced_performance_metrics():
    """Test enhanced performance metrics calculation"""
    try:
        logger.info("Testing enhanced performance metrics...")
        
        sr_service = SpacedRepetitionService()
        user_id = "test_user_metrics"
        
        # Create items with varied performance
        items = []
        for i in range(5):
            item = await sr_service.add_item_to_review(
                user_id=user_id,
                content_id=f"metrics_test_item_{i}",
                content_type=ContentType.QUIZ_QUESTION,
                initial_difficulty=2.5,
                metadata={"test": True}
            )
            
            # Simulate different performance levels
            for j in range(3):
                quality = ReviewQuality.PERFECT if i < 2 else \
                         ReviewQuality.EASY if i < 4 else \
                         ReviewQuality.DIFFICULT
                
                await sr_service.record_review(
                    item_id=item.id,
                    user_id=user_id,
                    quality=quality,
                    response_time_seconds=15 + i * 5
                )
            
            items.append(item)
        
        # Get enhanced performance metrics
        metrics = await sr_service.get_performance_metrics(user_id, days_back=30)
        
        logger.info("Enhanced performance metrics:")
        logger.info(f"  Total reviews: {metrics.total_reviews}")
        logger.info(f"  Correct reviews: {metrics.correct_reviews}")
        logger.info(f"  Accuracy rate: {metrics.accuracy_rate:.2%}")
        logger.info(f"  Average ease factor: {metrics.average_ease_factor:.2f}")
        logger.info(f"  Retention rate: {metrics.retention_rate:.2%}")
        logger.info(f"  Streak count: {metrics.streak_count}")
        
        # Get comprehensive stats
        stats = await sr_service.get_user_sr_stats(user_id)
        
        logger.info("Comprehensive SR stats:")
        logger.info(f"  Total items: {stats['total_items']}")
        logger.info(f"  Due items: {stats['due_items']}")
        logger.info(f"  Mature items: {stats['mature_items']}")
        logger.info(f"  Learning items: {stats['learning_items']}")
        logger.info(f"  Average session duration: {stats['average_session_duration']:.1f} minutes")
        
        if 'interval_distribution' in stats:
            logger.info("  Interval distribution:")
            for interval_range, count in stats['interval_distribution'].items():
                logger.info(f"    {interval_range} days: {count} items")
        
        return metrics.total_reviews > 0 and stats['total_items'] > 0
        
    except Exception as e:
        logger.error(f"Enhanced performance metrics test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_adaptive_scheduling():
    """Test adaptive scheduling based on performance"""
    try:
        logger.info("Testing adaptive scheduling...")
        
        sr_service = SpacedRepetitionService()
        user_id = "test_user_adaptive"
        
        # Create an item and track how scheduling adapts
        item = await sr_service.add_item_to_review(
            user_id=user_id,
            content_id="adaptive_test_item",
            content_type=ContentType.DEFINITION,
            initial_difficulty=2.5,
            metadata={"adaptive_test": True}
        )
        
        logger.info(f"Initial item state:")
        logger.info(f"  Ease factor: {item.ease_factor}")
        logger.info(f"  Interval: {item.interval}")
        logger.info(f"  Repetitions: {item.repetitions}")
        
        # Simulate a series of reviews with different qualities
        review_qualities = [
            ReviewQuality.PERFECT,
            ReviewQuality.EASY,
            ReviewQuality.PERFECT,
            ReviewQuality.HESITANT,
            ReviewQuality.PERFECT
        ]
        
        for i, quality in enumerate(review_qualities):
            item = await sr_service.record_review(
                item_id=item.id,
                user_id=user_id,
                quality=quality,
                response_time_seconds=20 - i * 2  # Getting faster over time
            )
            
            logger.info(f"After review {i+1} (quality {quality.value}):")
            logger.info(f"  Ease factor: {item.ease_factor:.2f}")
            logger.info(f"  Interval: {item.interval}")
            logger.info(f"  Repetitions: {item.repetitions}")
            logger.info(f"  Next review: {item.next_review_date.strftime('%Y-%m-%d')}")
        
        # Test that the algorithm adapted properly
        final_ease_factor = item.ease_factor
        final_interval = item.interval
        
        # Should have increased ease factor and interval due to good performance
        success = (final_ease_factor > sr_service.INITIAL_EASE_FACTOR and 
                  final_interval > 1 and 
                  item.repetitions == len(review_qualities))
        
        logger.info(f"Adaptive scheduling test: {'PASSED' if success else 'FAILED'}")
        return success
        
    except Exception as e:
        logger.error(f"Adaptive scheduling test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all enhanced tests"""
    logger.info("=== Enhanced Spaced Repetition Service Tests ===")
    
    # Test enhanced optimization
    optimization_success = await test_enhanced_optimization()
    
    # Test optimal session timing
    timing_success = await test_optimal_session_timing()
    
    # Test advanced retention analytics
    analytics_success = await test_advanced_retention_analytics()
    
    # Test enhanced performance metrics
    metrics_success = await test_enhanced_performance_metrics()
    
    # Test adaptive scheduling
    adaptive_success = await test_adaptive_scheduling()
    
    # Summary
    logger.info("=== Enhanced Test Summary ===")
    logger.info(f"Enhanced optimization: {'PASSED' if optimization_success else 'FAILED'}")
    logger.info(f"Optimal session timing: {'PASSED' if timing_success else 'FAILED'}")
    logger.info(f"Advanced retention analytics: {'PASSED' if analytics_success else 'FAILED'}")
    logger.info(f"Enhanced performance metrics: {'PASSED' if metrics_success else 'FAILED'}")
    logger.info(f"Adaptive scheduling: {'PASSED' if adaptive_success else 'FAILED'}")
    
    all_passed = all([
        optimization_success, timing_success, analytics_success,
        metrics_success, adaptive_success
    ])
    
    if all_passed:
        logger.info("All enhanced tests PASSED!")
        return 0
    else:
        logger.error("Some enhanced tests FAILED!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)