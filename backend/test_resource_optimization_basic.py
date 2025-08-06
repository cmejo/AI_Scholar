"""
Basic test for resource optimization service
"""
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from core.database import get_db, init_db
from core.database import (
    Institution, ResourceUsage, User, UserRole
)
from services.resource_optimization_service import ResourceOptimizationService

async def test_resource_optimization_basic():
    """Test basic resource optimization functionality"""
    print("Testing Resource Optimization Service...")
    
    # Initialize database
    await init_db()
    
    # Create test data
    db = next(get_db())
    
    try:
        # Clean up any existing test data
        import uuid
        test_suffix = str(uuid.uuid4())[:8]
        
        # Create test institution
        institution = Institution(
            name=f"Test University {test_suffix}",
            domain=f"test{test_suffix}.edu",
            type="university",
            settings={"budget_limit": 1000}
        )
        db.add(institution)
        db.commit()
        db.refresh(institution)
        
        # Create test users with unique emails
        user1 = User(
            email=f"student1_{test_suffix}@test.edu",
            name="Test Student 1",
            hashed_password="hashed_password"
        )
        user2 = User(
            email=f"faculty1_{test_suffix}@test.edu",
            name="Test Faculty 1",
            hashed_password="hashed_password"
        )
        db.add_all([user1, user2])
        db.commit()
        db.refresh(user1)
        db.refresh(user2)
        
        # Create user roles
        student_role = UserRole(
            user_id=user1.id,
            institution_id=institution.id,
            role_name="student",
            department="Computer Science",
            permissions={"basic_access": True}
        )
        faculty_role = UserRole(
            user_id=user2.id,
            institution_id=institution.id,
            role_name="faculty",
            department="Computer Science",
            permissions={"full_access": True}
        )
        db.add_all([student_role, faculty_role])
        db.commit()
        
        # Create test resource usage data
        base_time = datetime.now() - timedelta(days=15)
        
        usage_records = []
        for i in range(30):  # 30 days of data
            day_offset = timedelta(days=i)
            timestamp = base_time + day_offset
            
            # Student usage
            usage_records.extend([
                ResourceUsage(
                    user_id=user1.id,
                    institution_id=institution.id,
                    resource_type="ai_request",
                    resource_name="GPT Query",
                    usage_amount=5 + (i % 3),  # Varying usage
                    usage_unit="requests",
                    cost=0.25 + (i % 3) * 0.05,
                    timestamp=timestamp
                ),
                ResourceUsage(
                    user_id=user1.id,
                    institution_id=institution.id,
                    resource_type="document_upload",
                    resource_name="PDF Upload",
                    usage_amount=10 + (i % 5),
                    usage_unit="mb",
                    cost=0.1 + (i % 5) * 0.01,
                    timestamp=timestamp
                )
            ])
            
            # Faculty usage (higher usage)
            usage_records.extend([
                ResourceUsage(
                    user_id=user2.id,
                    institution_id=institution.id,
                    resource_type="database_query",
                    resource_name="Research DB",
                    usage_amount=20 + (i % 7),
                    usage_unit="queries",
                    cost=0.02 + (i % 7) * 0.001,
                    timestamp=timestamp
                ),
                ResourceUsage(
                    user_id=user2.id,
                    institution_id=institution.id,
                    resource_type="ai_request",
                    resource_name="Advanced AI",
                    usage_amount=15 + (i % 4),
                    usage_unit="requests",
                    cost=0.75 + (i % 4) * 0.05,
                    timestamp=timestamp
                )
            ])
        
        db.add_all(usage_records)
        db.commit()
        
        # Test resource optimization service
        optimization_service = ResourceOptimizationService()
        
        # Test 1: Analyze usage patterns
        print("\n1. Testing usage pattern analysis...")
        usage_analysis = await optimization_service.analyze_usage_patterns(institution.id)
        
        print(f"Usage statistics keys: {list(usage_analysis['usage_statistics'].keys())}")
        print(f"Total records analyzed: {usage_analysis['total_records_analyzed']}")
        print(f"Peak usage hours: {len(usage_analysis['peak_usage_hours'])}")
        print(f"Heavy users: {len(usage_analysis['heavy_users'])}")
        
        assert "usage_statistics" in usage_analysis
        assert usage_analysis["total_records_analyzed"] > 0
        assert len(usage_analysis["usage_statistics"]) > 0
        
        # Test 2: Resource allocation optimization
        print("\n2. Testing resource allocation optimization...")
        optimization_goals = {
            "budget_limit": 800,
            "performance_target": "balanced"
        }
        
        optimization_result = await optimization_service.optimize_resource_allocation(
            institution.id, optimization_goals
        )
        
        print(f"Current cost: ${optimization_result['current_cost']:.2f}")
        print(f"Potential savings: ${optimization_result['potential_savings']:.2f}")
        print(f"Number of recommendations: {len(optimization_result['optimization_recommendations'])}")
        
        assert "optimization_recommendations" in optimization_result
        assert "cost_benefit_analysis" in optimization_result
        assert optimization_result["current_cost"] > 0
        
        # Test 3: Usage forecasting
        print("\n3. Testing usage forecasting...")
        forecast_result = await optimization_service.forecast_usage(institution.id, 30)
        
        print(f"Forecast period: {forecast_result['forecast_period_days']} days")
        print(f"Forecasts generated: {len(forecast_result['forecasts'])}")
        print(f"Overall confidence: {forecast_result['overall_confidence']:.1f}%")
        print(f"Capacity recommendations: {len(forecast_result['capacity_recommendations'])}")
        
        assert "forecasts" in forecast_result
        assert forecast_result["forecast_period_days"] == 30
        
        # Test 4: Resource recommendations
        print("\n4. Testing resource recommendations...")
        user_context = {
            "user_id": user1.id,
            "role": "student",
            "department": "Computer Science"
        }
        
        recommendations = await optimization_service.recommend_resources(
            institution.id, user_context
        )
        
        print(f"Recommendations for user: {len(recommendations['recommendations'])}")
        print(f"Similar users found: {recommendations['peer_comparison']['similar_users_count']}")
        
        assert "recommendations" in recommendations
        assert "peer_comparison" in recommendations
        
        print("\n✅ All resource optimization tests passed!")
        
        # Test specific optimization scenarios
        print("\n5. Testing specific optimization scenarios...")
        
        # Add some extreme usage to test optimization recommendations
        extreme_usage = ResourceUsage(
            user_id=user1.id,
            institution_id=institution.id,
            resource_type="storage",
            resource_name="Large Dataset",
            usage_amount=1000,  # Very high usage
            usage_unit="gb",
            cost=20.0,
            timestamp=datetime.now()
        )
        db.add(extreme_usage)
        db.commit()
        
        # Re-run optimization
        optimization_result_2 = await optimization_service.optimize_resource_allocation(
            institution.id, optimization_goals
        )
        
        print(f"Updated recommendations: {len(optimization_result_2['optimization_recommendations'])}")
        
        # Check if new recommendations were generated
        storage_recommendations = [
            r for r in optimization_result_2['optimization_recommendations'] 
            if 'storage' in r.get('resource', '')
        ]
        print(f"Storage-related recommendations: {len(storage_recommendations)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = asyncio.run(test_resource_optimization_basic())
    if success:
        print("\n🎉 Resource optimization service is working correctly!")
    else:
        print("\n💥 Resource optimization service test failed!")