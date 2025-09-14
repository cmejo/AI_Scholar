#!/usr/bin/env python3
"""
Simple test to verify research endpoints can be imported and basic functionality works
"""
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    
    try:
        from fastapi import APIRouter, HTTPException
        print("✅ FastAPI imports successful")
    except ImportError as e:
        print(f"❌ FastAPI import failed: {e}")
        return False
    
    try:
        from api.advanced_endpoints import router
        print("✅ Advanced endpoints import successful")
    except ImportError as e:
        print(f"❌ Advanced endpoints import failed: {e}")
        return False
    
    try:
        from core import service_manager
        print("✅ Service manager import successful")
    except ImportError as e:
        print(f"❌ Service manager import failed: {e}")
        return False
    
    try:
        from models.schemas import DetailedHealthCheckResponse
        print("✅ Schemas import successful")
    except ImportError as e:
        print(f"❌ Schemas import failed: {e}")
        return False
    
    return True

def test_endpoint_structure():
    """Test that the research endpoints are properly structured"""
    print("\nTesting endpoint structure...")
    
    try:
        from api.advanced_endpoints import router
        
        # Check if router has the expected routes
        routes = [route.path for route in router.routes]
        
        expected_routes = [
            "/research/status",
            "/research/capabilities", 
            "/research/search/basic",
            "/research/domains",
            "/research/validate"
        ]
        
        found_routes = []
        for expected in expected_routes:
            full_path = f"/api/advanced{expected}"
            if any(expected in route for route in routes):
                found_routes.append(expected)
                print(f"✅ Found route: {expected}")
            else:
                print(f"❌ Missing route: {expected}")
        
        if len(found_routes) == len(expected_routes):
            print("✅ All expected research endpoints found")
            return True
        else:
            print(f"❌ Found {len(found_routes)}/{len(expected_routes)} expected routes")
            return False
            
    except Exception as e:
        print(f"❌ Error testing endpoint structure: {e}")
        return False

def main():
    """Main test function"""
    print("Basic Research Endpoints Test")
    print("=" * 40)
    
    # Test imports
    if not test_imports():
        print("\n❌ Import tests failed")
        return False
    
    # Test endpoint structure
    if not test_endpoint_structure():
        print("\n❌ Endpoint structure tests failed")
        return False
    
    print("\n🎉 All basic tests passed!")
    print("Research endpoints are properly implemented and can be imported.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)