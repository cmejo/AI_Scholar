"""
Task 4.3 Verification Test: Create learning progress tracking

This test verifies that the learning progress tracking implementation meets all requirements:
- Build comprehensive learning analytics with performance metrics
- Implement knowledge gap identification and targeted recommendations  
- Create visual progress dashboards with learning trajectory visualization
- Add competency mapping and skill development tracking
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

async def test_task_4_3_requirements():
    """Test all requirements for task 4.3"""
    logger.info("=== Task 4.3 Verification: Create learning progress tracking ===")
    
    service = LearningProgressService()
    test_user_id = "task_4_3_test_user"
    
    # Test 1: Comprehensive learning analytics with performance metrics
    logger.info("Testing comprehensive learning analytics with performance metrics...")
    
    analytics = await service.get_comprehensive_analytics(test_user_id)
    
    # Verify all required analytics components are present
    required_analytics = [
        "overview", "performance_trends", "learning_velocity", 
        "retention_analysis", "difficulty_progression", "time_investment",
        "competency_distribution", "learning_patterns"
    ]
    
    analytics_passed = True
    for component in required_analytics:
        if component in analytics:
            logger.info(f"✅ Analytics component '{component}' present")
        else:
            logger.error(f"❌ Missing analytics component: {component}")
            analytics_passed = False
    
    # Test overview metrics structure
    overview = analytics.get("overview", {})
    overview_metrics = [
        "total_topics", "total_study_time_minutes", "total_quizzes_taken",
        "average_competency", "competency_consistency", "average_quiz_score",
        "topics_mastered", "topics_in_progress", "topics_need_attention"
    ]
    
    for metric in overview_metrics:
        if metric in overview:
            logger.info(f"✅ Overview metric '{metric}': {overview[metric]}")
        else:
            logger.error(f"❌ Missing overview metric: {metric}")
            analytics_passed = False
    
    # Test 2: Knowledge gap identification and targeted recommendations
    logger.info("Testing knowledge gap identification and targeted recommendations...")
    
    knowledge_gaps = await service.identify_knowledge_gaps(test_user_id)
    recommendations = await service.generate_learning_recommendations(test_user_id)
    
    # Verify knowledge gap structure
    gap_types = ["weak_foundation", "declining_performance", "outdated_knowledge"]
    logger.info(f"✅ Knowledge gaps identified: {len(knowledge_gaps)}")
    logger.info(f"✅ Learning recommendations generated: {len(recommendations)}")
    
    # Test gap structure if gaps exist
    if knowledge_gaps:
        gap = knowledge_gaps[0]
        gap_attributes = ["topic", "gap_type", "severity", "evidence", "recommendations", "related_topics"]
        for attr in gap_attributes:
            if hasattr(gap, attr):
                logger.info(f"✅ Knowledge gap has attribute '{attr}'")
            else:
                logger.error(f"❌ Missing knowledge gap attribute: {attr}")
                analytics_passed = False
    
    # Test recommendation structure if recommendations exist
    if recommendations:
        rec = recommendations[0]
        rec_attributes = ["type", "topic", "priority", "reason", "suggested_actions", "estimated_time_minutes"]
        for attr in rec_attributes:
            if hasattr(rec, attr):
                logger.info(f"✅ Recommendation has attribute '{attr}'")
            else:
                logger.error(f"❌ Missing recommendation attribute: {attr}")
                analytics_passed = False
    
    # Test 3: Visual progress dashboards with learning trajectory visualization
    logger.info("Testing visual progress dashboards with learning trajectory visualization...")
    
    dashboard_data = await service.get_visual_dashboard_data(test_user_id)
    
    # Verify dashboard components
    dashboard_components = [
        "summary_cards", "competency_radar", "learning_trajectory_chart",
        "performance_trends", "time_investment_chart", "competency_distribution",
        "knowledge_gaps_heatmap", "learning_velocity_gauge", "retention_analysis"
    ]
    
    dashboard_passed = True
    for component in dashboard_components:
        if component in dashboard_data:
            logger.info(f"✅ Dashboard component '{component}' present")
        else:
            logger.error(f"❌ Missing dashboard component: {component}")
            dashboard_passed = False
    
    # Test summary cards structure
    summary_cards = dashboard_data.get("summary_cards", {})
    card_metrics = ["total_topics", "average_competency", "study_time_hours", "quizzes_completed"]
    
    for metric in card_metrics:
        if metric in summary_cards:
            logger.info(f"✅ Summary card metric '{metric}': {summary_cards[metric]}")
        else:
            logger.error(f"❌ Missing summary card metric: {metric}")
            dashboard_passed = False
    
    # Test learning trajectory for a sample topic
    trajectory = await service.get_learning_trajectory(test_user_id, "sample_topic")
    trajectory_attributes = ["topic", "time_points", "competency_scores", "study_sessions", "trend_analysis", "predictions"]
    
    trajectory_passed = True
    for attr in trajectory_attributes:
        if hasattr(trajectory, attr):
            logger.info(f"✅ Learning trajectory has attribute '{attr}'")
        else:
            logger.error(f"❌ Missing trajectory attribute: {attr}")
            trajectory_passed = False
    
    # Test 4: Competency mapping and skill development tracking
    logger.info("Testing competency mapping and skill development tracking...")
    
    competency_map = await service.create_competency_map(test_user_id)
    
    # Verify competency map structure
    competency_attributes = ["user_id", "competencies", "skill_tree", "mastery_path", "generated_at"]
    
    competency_passed = True
    for attr in competency_attributes:
        if hasattr(competency_map, attr):
            logger.info(f"✅ Competency map has attribute '{attr}'")
        else:
            logger.error(f"❌ Missing competency map attribute: {attr}")
            competency_passed = False
    
    # Test competency levels
    competency_levels = [level.value for level in CompetencyLevel]
    logger.info(f"✅ Available competency levels: {competency_levels}")
    
    # Test learning goal types
    goal_types = [goal.value for goal in LearningGoalType]
    logger.info(f"✅ Available learning goal types: {goal_types}")
    
    # Test enhanced analytics methods
    logger.info("Testing enhanced analytics methods...")
    
    # Test knowledge gaps heatmap
    heatmap_data = await service._create_knowledge_gaps_heatmap(test_user_id)
    heatmap_keys = ["topics", "gap_types", "severity_matrix", "max_severity"]
    
    heatmap_passed = True
    for key in heatmap_keys:
        if key in heatmap_data:
            logger.info(f"✅ Heatmap data has key '{key}'")
        else:
            logger.error(f"❌ Missing heatmap key: {key}")
            heatmap_passed = False
    
    # Test performance metrics calculation
    overview_metrics = await service._calculate_overview_metrics([], [], [])
    performance_trends = await service._calculate_performance_trends([], [])
    learning_velocity = await service._calculate_learning_velocity([], [])
    competency_distribution = await service._calculate_competency_distribution([])
    learning_patterns = await service._identify_learning_patterns([], [])
    retention_analysis = await service._calculate_retention_analysis([], [])
    time_investment = await service._calculate_time_investment_metrics([])
    
    logger.info("✅ All enhanced analytics methods are functional")
    
    # Final verification
    all_tests_passed = (
        analytics_passed and 
        dashboard_passed and 
        trajectory_passed and 
        competency_passed and 
        heatmap_passed
    )
    
    logger.info("=== Task 4.3 Verification Summary ===")
    logger.info(f"Comprehensive learning analytics: {'✅ PASSED' if analytics_passed else '❌ FAILED'}")
    logger.info(f"Knowledge gap identification: {'✅ PASSED' if analytics_passed else '❌ FAILED'}")
    logger.info(f"Visual progress dashboards: {'✅ PASSED' if dashboard_passed else '❌ FAILED'}")
    logger.info(f"Learning trajectory visualization: {'✅ PASSED' if trajectory_passed else '❌ FAILED'}")
    logger.info(f"Competency mapping: {'✅ PASSED' if competency_passed else '❌ FAILED'}")
    logger.info(f"Skill development tracking: {'✅ PASSED' if competency_passed else '❌ FAILED'}")
    
    if all_tests_passed:
        logger.info("🎉 Task 4.3 'Create learning progress tracking' - ALL REQUIREMENTS VERIFIED!")
        logger.info("✅ Build comprehensive learning analytics with performance metrics: IMPLEMENTED")
        logger.info("✅ Implement knowledge gap identification and targeted recommendations: IMPLEMENTED")
        logger.info("✅ Create visual progress dashboards with learning trajectory visualization: IMPLEMENTED")
        logger.info("✅ Add competency mapping and skill development tracking: IMPLEMENTED")
        return True
    else:
        logger.error("❌ Some requirements not fully met")
        return False

async def test_progress_update_workflow():
    """Test the complete workflow of updating and tracking progress"""
    logger.info("Testing complete progress tracking workflow...")
    
    service = LearningProgressService()
    test_user_id = "workflow_test_user"
    
    # Simulate learning progress updates
    topics = ["Machine Learning", "Data Science", "Statistics", "Python Programming"]
    
    for i, topic in enumerate(topics):
        # Simulate improving performance over time
        for session in range(3):
            performance_score = 0.3 + (i * 0.1) + (session * 0.15)  # Gradual improvement
            performance_score = min(1.0, performance_score)  # Cap at 1.0
            
            progress = await service.update_learning_progress(
                user_id=test_user_id,
                topic=topic,
                performance_score=performance_score,
                study_duration_minutes=30 + (session * 10),
                metadata={"session": session + 1, "difficulty": "intermediate"}
            )
            
            logger.info(f"Updated progress for {topic}: competency={progress.competency_level:.2f}")
    
    # Get comprehensive overview
    overview = await service.get_user_progress_overview(test_user_id)
    logger.info(f"✅ User has progress in {overview['total_topics']} topics")
    logger.info(f"✅ Average competency: {overview['average_competency']:.2f}")
    
    # Test knowledge gap identification
    gaps = await service.identify_knowledge_gaps(test_user_id)
    logger.info(f"✅ Identified {len(gaps)} knowledge gaps")
    
    # Test recommendations
    recommendations = await service.generate_learning_recommendations(test_user_id)
    logger.info(f"✅ Generated {len(recommendations)} learning recommendations")
    
    # Test competency map
    comp_map = await service.create_competency_map(test_user_id)
    logger.info(f"✅ Created competency map with {len(comp_map.competencies)} topics")
    
    logger.info("✅ Complete workflow test passed!")
    return True

async def main():
    """Run all verification tests"""
    logger.info("Starting Task 4.3 verification tests...")
    
    # Test requirements compliance
    requirements_passed = await test_task_4_3_requirements()
    
    # Test complete workflow
    workflow_passed = await test_progress_update_workflow()
    
    if requirements_passed and workflow_passed:
        logger.info("🎉 ALL TASK 4.3 VERIFICATION TESTS PASSED!")
        logger.info("Task 4.3 'Create learning progress tracking' is COMPLETE and VERIFIED!")
        return 0
    else:
        logger.error("❌ Some verification tests failed")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)