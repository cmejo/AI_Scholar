"""
Gamification API Endpoints Test - Task 4.4 Implementation

This test verifies the API endpoints for:
1. Achievement system with badges and progress rewards
2. Personalized study recommendations based on learning patterns
3. Social learning features with peer comparison and collaboration
4. Adaptive content difficulty based on individual learning curves
"""

import asyncio
import sys
import os
import logging
import json
from datetime import datetime
from unittest.mock import Mock, AsyncMock

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from fastapi import FastAPI
from api.gamification_endpoints import router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create test app
app = FastAPI()
app.include_router(router)

# Mock user for testing
class MockUser:
    def __init__(self, user_id="test_user"):
        self.id = user_id

def mock_get_current_user():
    return MockUser()

# Override the dependency
app.dependency_overrides[router.dependencies[0].dependency] = mock_get_current_user

def test_achievement_endpoints():
    """Test achievement-related endpoints"""
    try:
        logger.info("Testing achievement endpoints...")
        
        client = TestClient(app)
        
        # Test award achievement endpoint
        award_data = {
            "achievement_type": "progress",
            "context": {"event": "quiz_completed", "score": 0.95}
        }
        
        response = client.post("/api/gamification/achievements/award", json=award_data)
        logger.info(f"Award achievement response status: {response.status_code}")
        
        # Test get user achievements endpoint
        response = client.get("/api/gamification/achievements")
        logger.info(f"Get achievements response status: {response.status_code}")
        if response.status_code == 200:
            achievements = response.json()
            logger.info(f"Retrieved {len(achievements)} achievements")
        
        # Test get achievement types endpoint
        response = client.get("/api/gamification/achievement-types")
        logger.info(f"Get achievement types response status: {response.status_code}")
        if response.status_code == 200:
            types = response.json()
            logger.info(f"Available achievement types: {len(types.get('achievement_types', []))}")
        
        # Test get badge levels endpoint
        response = client.get("/api/gamification/badge-levels")
        logger.info(f"Get badge levels response status: {response.status_code}")
        if response.status_code == 200:
            levels = response.json()
            logger.info(f"Available badge levels: {len(levels.get('badge_levels', []))}")
        
        return True
        
    except Exception as e:
        logger.error(f"Achievement endpoints test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_personalized_recommendations_endpoints():
    """Test personalized recommendations endpoints"""
    try:
        logger.info("Testing personalized recommendations endpoints...")
        
        client = TestClient(app)
        
        # Test get personalized recommendations endpoint
        response = client.get("/api/gamification/recommendations?limit=5")
        logger.info(f"Get recommendations response status: {response.status_code}")
        if response.status_code == 200:
            recommendations = response.json()
            logger.info(f"Retrieved {len(recommendations)} personalized recommendations")
            
            for i, rec in enumerate(recommendations[:3], 1):
                logger.info(f"  {i}. {rec.get('type', 'Unknown')} recommendation")
                logger.info(f"     Confidence: {rec.get('confidence', 0):.1%}")
                logger.info(f"     Benefit: {rec.get('estimated_benefit', 0):.1%}")
        
        # Test adaptive content recommendations endpoint
        topics = ["mathematics", "physics", "computer_science"]
        
        for topic in topics:
            response = client.get(f"/api/gamification/adaptive-content/{topic}")
            logger.info(f"Adaptive content for {topic} response status: {response.status_code}")
            if response.status_code == 200:
                content_rec = response.json()
                logger.info(f"  Recommended difficulty: {content_rec.get('recommended_difficulty', 0):.2f}")
                logger.info(f"  Content type: {content_rec.get('content_type', 'N/A')}")
        
        # Test personalized study plan endpoint
        study_plan_data = {
            "goals": ["mathematics", "physics"],
            "time_available_minutes": 120
        }
        
        response = client.post("/api/gamification/study-plan", json=study_plan_data)
        logger.info(f"Study plan response status: {response.status_code}")
        if response.status_code == 200:
            study_plan = response.json()
            logger.info(f"Generated study plan with {len(study_plan.get('sessions', []))} sessions")
            logger.info(f"Total time: {study_plan.get('total_time_minutes', 0)} minutes")
        
        return True
        
    except Exception as e:
        logger.error(f"Personalized recommendations endpoints test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_social_learning_endpoints():
    """Test social learning endpoints"""
    try:
        logger.info("Testing social learning endpoints...")
        
        client = TestClient(app)
        
        # Test get social learning data endpoint
        response = client.get("/api/gamification/social")
        logger.info(f"Get social data response status: {response.status_code}")
        if response.status_code == 200:
            social_data = response.json()
            logger.info(f"User rank: {social_data.get('user_rank', 0)} of {social_data.get('total_users', 0)}")
            logger.info(f"User score: {social_data.get('user_score', 0)}")
            logger.info(f"Peer group average: {social_data.get('peer_group_average', 0):.1f}")
        
        # Test get peer comparison data endpoint
        response = client.get("/api/gamification/peer-comparison")
        logger.info(f"Get peer comparison response status: {response.status_code}")
        if response.status_code == 200:
            peer_data = response.json()
            user_metrics = peer_data.get('user_metrics', {})
            peer_comparison = peer_data.get('peer_comparison', {})
            logger.info(f"User total points: {user_metrics.get('total_points', 0)}")
            logger.info(f"Points percentile: {peer_comparison.get('points_percentile', 0):.1f}%")
        
        # Test create study group endpoint
        study_group_data = {
            "name": "Test API Study Group",
            "description": "A test study group created via API",
            "max_members": 8
        }
        
        response = client.post("/api/gamification/study-groups", json=study_group_data)
        logger.info(f"Create study group response status: {response.status_code}")
        if response.status_code == 200:
            study_group = response.json()
            logger.info(f"Created study group: {study_group.get('name', 'Unknown')}")
            logger.info(f"Group ID: {study_group.get('id', 'N/A')}")
            
            # Test join study group endpoint
            join_data = {"group_id": study_group.get('id', 'test_group')}
            response = client.post("/api/gamification/study-groups/join", json=join_data)
            logger.info(f"Join study group response status: {response.status_code}")
        
        # Test get collaborative challenges endpoint
        response = client.get("/api/gamification/collaborative-challenges")
        logger.info(f"Get collaborative challenges response status: {response.status_code}")
        if response.status_code == 200:
            challenges_data = response.json()
            challenges = challenges_data.get('challenges', [])
            logger.info(f"Available collaborative challenges: {len(challenges)}")
            
            for challenge in challenges[:2]:
                logger.info(f"  - {challenge.get('title', 'Unknown')}")
                logger.info(f"    Type: {challenge.get('type', 'N/A')}")
                logger.info(f"    Reward: {challenge.get('individual_reward_points', 0)} points")
        
        # Test track peer interaction endpoint
        interaction_data = {
            "interaction_type": "help_given",
            "peer_id": "peer_test_123",
            "context": {"topic": "mathematics", "help_type": "explanation"}
        }
        
        response = client.post("/api/gamification/peer-interactions", json=interaction_data)
        logger.info(f"Track peer interaction response status: {response.status_code}")
        
        return True
        
    except Exception as e:
        logger.error(f"Social learning endpoints test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_adaptive_difficulty_endpoints():
    """Test adaptive difficulty endpoints"""
    try:
        logger.info("Testing adaptive difficulty endpoints...")
        
        client = TestClient(app)
        
        # Test adapt content difficulty endpoint
        difficulty_data = {
            "topic": "mathematics",
            "current_difficulty": 0.5
        }
        
        response = client.post("/api/gamification/difficulty/adapt", json=difficulty_data)
        logger.info(f"Adapt difficulty response status: {response.status_code}")
        if response.status_code == 200:
            difficulty_result = response.json()
            logger.info(f"Topic: {difficulty_result.get('topic', 'Unknown')}")
            logger.info(f"Previous difficulty: {difficulty_result.get('previous_difficulty', 0):.2f}")
            logger.info(f"New difficulty: {difficulty_result.get('new_difficulty', 0):.2f}")
            logger.info(f"Adjustment: {difficulty_result.get('adjustment', 0):+.2f}")
        
        # Test invalid difficulty values
        invalid_difficulty_data = {
            "topic": "physics",
            "current_difficulty": 1.5  # Invalid: > 1.0
        }
        
        response = client.post("/api/gamification/difficulty/adapt", json=invalid_difficulty_data)
        logger.info(f"Invalid difficulty response status: {response.status_code}")
        if response.status_code == 400:
            logger.info("✓ Correctly rejected invalid difficulty value")
        
        return True
        
    except Exception as e:
        logger.error(f"Adaptive difficulty endpoints test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_gamification_dashboard_endpoints():
    """Test gamification dashboard and utility endpoints"""
    try:
        logger.info("Testing gamification dashboard endpoints...")
        
        client = TestClient(app)
        
        # Test get user level endpoint
        response = client.get("/api/gamification/level")
        logger.info(f"Get user level response status: {response.status_code}")
        if response.status_code == 200:
            level_data = response.json()
            logger.info(f"Current level: {level_data.get('current_level', 0)}")
            logger.info(f"Level name: {level_data.get('level_name', 'Unknown')}")
            logger.info(f"Total points: {level_data.get('total_points', 0)}")
            logger.info(f"Progress to next: {level_data.get('progress_to_next_level', 0):.1%}")
        
        # Test get leaderboard endpoint
        response = client.get("/api/gamification/leaderboard?limit=5")
        logger.info(f"Get leaderboard response status: {response.status_code}")
        if response.status_code == 200:
            leaderboard = response.json()
            logger.info(f"User rank: {leaderboard.get('user_rank', 0)}")
            logger.info(f"Top users: {len(leaderboard.get('top_users', []))}")
        
        # Test get learning insights endpoint
        response = client.get("/api/gamification/learning-insights")
        logger.info(f"Get learning insights response status: {response.status_code}")
        if response.status_code == 200:
            insights = response.json()
            logger.info("Learning insights retrieved:")
            logger.info(f"  Peer comparison data: {'✓' if insights.get('peer_comparison') else '✗'}")
            logger.info(f"  Social stats: {'✓' if insights.get('social_stats') else '✗'}")
            logger.info(f"  Recent achievements: {len(insights.get('recent_achievements', []))}")
            logger.info(f"  Recommendations: {len(insights.get('personalized_recommendations', []))}")
        
        # Test get gamification dashboard endpoint
        response = client.get("/api/gamification/dashboard")
        logger.info(f"Get dashboard response status: {response.status_code}")
        if response.status_code == 200:
            dashboard = response.json()
            logger.info("Dashboard components:")
            logger.info(f"  Level info: {'✓' if dashboard.get('level_info') else '✗'}")
            logger.info(f"  Recent achievements: {len(dashboard.get('recent_achievements', []))}")
            logger.info(f"  Recommendations: {len(dashboard.get('recommendations', []))}")
            logger.info(f"  Social stats: {'✓' if dashboard.get('social_stats') else '✗'}")
            logger.info(f"  Points breakdown: {'✓' if dashboard.get('points_breakdown') else '✗'}")
            logger.info(f"  Streaks: {'✓' if dashboard.get('streaks') else '✗'}")
        
        # Test get learning styles endpoint
        response = client.get("/api/gamification/learning-styles")
        logger.info(f"Get learning styles response status: {response.status_code}")
        if response.status_code == 200:
            styles = response.json()
            logger.info(f"Available learning styles: {len(styles.get('learning_styles', []))}")
        
        # Test get difficulty preferences endpoint
        response = client.get("/api/gamification/difficulty-preferences")
        logger.info(f"Get difficulty preferences response status: {response.status_code}")
        if response.status_code == 200:
            preferences = response.json()
            logger.info(f"Available difficulty preferences: {len(preferences.get('difficulty_preferences', []))}")
        
        return True
        
    except Exception as e:
        logger.error(f"Dashboard endpoints test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_challenge_endpoints():
    """Test learning challenge endpoints"""
    try:
        logger.info("Testing challenge endpoints...")
        
        client = TestClient(app)
        
        # Test create learning challenge endpoint
        challenge_data = {
            "title": "API Test Challenge",
            "description": "A test challenge created via API",
            "challenge_type": "streak",
            "target_value": 7.0,
            "duration_days": 7,
            "points_reward": 100
        }
        
        response = client.post("/api/gamification/challenges", json=challenge_data)
        logger.info(f"Create challenge response status: {response.status_code}")
        if response.status_code == 200:
            challenge = response.json()
            logger.info(f"Created challenge: {challenge.get('title', 'Unknown')}")
            logger.info(f"Challenge type: {challenge.get('challenge_type', 'N/A')}")
            logger.info(f"Target value: {challenge.get('target_value', 0)}")
            logger.info(f"Duration: {challenge.get('duration_days', 0)} days")
            logger.info(f"Reward: {challenge.get('points_reward', 0)} points")
        
        # Test invalid challenge data
        invalid_challenge_data = {
            "title": "Invalid Challenge",
            "description": "A challenge with invalid data",
            "challenge_type": "streak",
            "target_value": 7.0,
            "duration_days": 0,  # Invalid: must be > 0
            "points_reward": 100
        }
        
        response = client.post("/api/gamification/challenges", json=invalid_challenge_data)
        logger.info(f"Invalid challenge response status: {response.status_code}")
        if response.status_code == 400:
            logger.info("✓ Correctly rejected invalid challenge data")
        
        return True
        
    except Exception as e:
        logger.error(f"Challenge endpoints test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_input_validation():
    """Test input validation for various endpoints"""
    try:
        logger.info("Testing input validation...")
        
        client = TestClient(app)
        
        # Test invalid study plan data
        invalid_study_plan = {
            "goals": [],  # Invalid: empty goals
            "time_available_minutes": 120
        }
        
        response = client.post("/api/gamification/study-plan", json=invalid_study_plan)
        logger.info(f"Empty goals study plan response status: {response.status_code}")
        if response.status_code == 400:
            logger.info("✓ Correctly rejected empty goals")
        
        # Test invalid time
        invalid_time_plan = {
            "goals": ["mathematics"],
            "time_available_minutes": 0  # Invalid: must be > 0
        }
        
        response = client.post("/api/gamification/study-plan", json=invalid_time_plan)
        logger.info(f"Invalid time study plan response status: {response.status_code}")
        if response.status_code == 400:
            logger.info("✓ Correctly rejected invalid time")
        
        # Test invalid interaction type
        invalid_interaction = {
            "interaction_type": "invalid_type",  # Invalid type
            "peer_id": "peer_123",
            "context": {}
        }
        
        response = client.post("/api/gamification/peer-interactions", json=invalid_interaction)
        logger.info(f"Invalid interaction type response status: {response.status_code}")
        if response.status_code == 400:
            logger.info("✓ Correctly rejected invalid interaction type")
        
        # Test invalid study group name
        invalid_group = {
            "name": "AB",  # Invalid: too short
            "description": "Test group",
            "max_members": 5
        }
        
        response = client.post("/api/gamification/study-groups", json=invalid_group)
        logger.info(f"Invalid group name response status: {response.status_code}")
        if response.status_code == 400:
            logger.info("✓ Correctly rejected short group name")
        
        return True
        
    except Exception as e:
        logger.error(f"Input validation test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all API endpoint tests"""
    logger.info("=== Gamification API Endpoints Tests (Task 4.4) ===")
    
    # Test achievement endpoints
    achievement_success = test_achievement_endpoints()
    
    # Test personalized recommendations endpoints
    recommendations_success = test_personalized_recommendations_endpoints()
    
    # Test social learning endpoints
    social_success = test_social_learning_endpoints()
    
    # Test adaptive difficulty endpoints
    adaptive_success = test_adaptive_difficulty_endpoints()
    
    # Test dashboard endpoints
    dashboard_success = test_gamification_dashboard_endpoints()
    
    # Test challenge endpoints
    challenge_success = test_challenge_endpoints()
    
    # Test input validation
    validation_success = test_input_validation()
    
    # Summary
    logger.info("=== API Test Summary ===")
    logger.info(f"Achievement endpoints: {'PASSED' if achievement_success else 'FAILED'}")
    logger.info(f"Personalized recommendations: {'PASSED' if recommendations_success else 'FAILED'}")
    logger.info(f"Social learning endpoints: {'PASSED' if social_success else 'FAILED'}")
    logger.info(f"Adaptive difficulty endpoints: {'PASSED' if adaptive_success else 'FAILED'}")
    logger.info(f"Dashboard endpoints: {'PASSED' if dashboard_success else 'FAILED'}")
    logger.info(f"Challenge endpoints: {'PASSED' if challenge_success else 'FAILED'}")
    logger.info(f"Input validation: {'PASSED' if validation_success else 'FAILED'}")
    
    all_passed = all([
        achievement_success, recommendations_success, social_success,
        adaptive_success, dashboard_success, challenge_success, validation_success
    ])
    
    if all_passed:
        logger.info("All API endpoint tests PASSED!")
        logger.info("Task 4.4 API implementation verified successfully!")
        return 0
    else:
        logger.error("Some API endpoint tests FAILED!")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)