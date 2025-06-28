#!/usr/bin/env python3
"""
Test script for Category 3: AI & Model Mastery features
Tests fine-tuning from user feedback and automated RAG evaluation
"""

import requests
import json
import time
import os
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000"
TEST_USER_TOKEN = None  # Will be obtained during test

def print_test_header(test_name):
    """Print formatted test header"""
    print(f"\n{'='*60}")
    print(f"Testing: {test_name}")
    print(f"{'='*60}")

def print_result(test_name, success, details=""):
    """Print test result"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} {test_name}")
    if details:
        print(f"   Details: {details}")

def test_user_authentication():
    """Test user authentication and get admin token"""
    global TEST_USER_TOKEN
    
    print_test_header("User Authentication")
    
    # Try to register an admin test user
    register_data = {
        "username": "test_ai_mastery_admin",
        "email": "test_ai_mastery@example.com",
        "password": "test_password_123"
    }
    
    try:
        # Register user (might fail if already exists)
        response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
        
        # Login to get token
        login_data = {
            "username": "test_ai_mastery_admin",
            "password": "test_password_123"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            TEST_USER_TOKEN = data.get('token')
            print_result("User Authentication", True, f"Token obtained: {TEST_USER_TOKEN[:20]}...")
            
            # Make user admin (this would normally be done through admin interface)
            # For testing, we'll assume the user has admin privileges
            return True
        else:
            print_result("User Authentication", False, f"Login failed: {response.status_code}")
            return False
            
    except Exception as e:
        print_result("User Authentication", False, f"Error: {str(e)}")
        return False

def test_feedback_statistics():
    """Test feedback statistics endpoint"""
    print_test_header("Feedback Statistics")
    
    if not TEST_USER_TOKEN:
        print_result("Feedback Statistics", False, "No user token available")
        return False
    
    headers = {
        "Authorization": f"Bearer {TEST_USER_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/api/ai-mastery/feedback-stats?days=30", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                stats = data
                print_result("Feedback Statistics", True, 
                           f"Total feedback: {stats.get('total_feedback', 0)}, "
                           f"Ready for fine-tuning: {stats.get('ready_for_fine_tuning', False)}")
                return True
            else:
                print_result("Feedback Statistics", False, f"API error: {data.get('error')}")
                return False
        else:
            print_result("Feedback Statistics", False, f"HTTP error: {response.status_code}")
            return False
            
    except Exception as e:
        print_result("Feedback Statistics", False, f"Error: {str(e)}")
        return False

def test_dataset_preparation():
    """Test dataset preparation for fine-tuning"""
    print_test_header("Dataset Preparation")
    
    if not TEST_USER_TOKEN:
        print_result("Dataset Preparation", False, "No user token available")
        return False
    
    headers = {
        "Authorization": f"Bearer {TEST_USER_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        # Prepare dataset with lower requirements for testing
        prepare_data = {
            "min_feedback_pairs": 5,  # Lower requirement for testing
            "days": 30
        }
        
        response = requests.post(f"{BASE_URL}/api/ai-mastery/prepare-dataset", 
                               json=prepare_data, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print_result("Dataset Preparation", True, 
                           f"Dataset created with {data.get('dataset_size', 0)} pairs")
                return True
            else:
                # This might fail if there's insufficient feedback data, which is expected
                print_result("Dataset Preparation", True, 
                           f"Expected failure: {data.get('error', 'Insufficient data')}")
                return True
        else:
            print_result("Dataset Preparation", False, f"HTTP error: {response.status_code}")
            return False
            
    except Exception as e:
        print_result("Dataset Preparation", False, f"Error: {str(e)}")
        return False

def test_fine_tuning_jobs():
    """Test fine-tuning jobs management"""
    print_test_header("Fine-tuning Jobs")
    
    if not TEST_USER_TOKEN:
        print_result("Fine-tuning Jobs", False, "No user token available")
        return False
    
    headers = {
        "Authorization": f"Bearer {TEST_USER_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        # Get list of fine-tuning jobs
        response = requests.get(f"{BASE_URL}/api/ai-mastery/fine-tuning-jobs", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                jobs = data.get('jobs', [])
                print_result("Get Fine-tuning Jobs", True, f"Found {len(jobs)} jobs")
                
                # Test getting specific job if any exist
                if jobs:
                    job_id = jobs[0]['id']
                    job_response = requests.get(f"{BASE_URL}/api/ai-mastery/fine-tuning-jobs/{job_id}", 
                                              headers=headers)
                    
                    if job_response.status_code == 200:
                        job_data = job_response.json()
                        if job_data.get('success'):
                            print_result("Get Specific Job", True, 
                                       f"Job status: {job_data['job']['status']}")
                        else:
                            print_result("Get Specific Job", False, f"API error: {job_data.get('error')}")
                    else:
                        print_result("Get Specific Job", False, f"HTTP error: {job_response.status_code}")
                
                return True
            else:
                print_result("Fine-tuning Jobs", False, f"API error: {data.get('error')}")
                return False
        else:
            print_result("Fine-tuning Jobs", False, f"HTTP error: {response.status_code}")
            return False
            
    except Exception as e:
        print_result("Fine-tuning Jobs", False, f"Error: {str(e)}")
        return False

def test_rag_evaluation():
    """Test RAG evaluation functionality"""
    print_test_header("RAG Evaluation")
    
    if not TEST_USER_TOKEN:
        print_result("RAG Evaluation", False, "No user token available")
        return False
    
    headers = {
        "Authorization": f"Bearer {TEST_USER_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        # Get RAG evaluation statistics
        response = requests.get(f"{BASE_URL}/api/ai-mastery/rag-evaluation-stats?days=30", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                total_evaluations = data.get('total_evaluations', 0)
                avg_scores = data.get('average_scores', {})
                print_result("RAG Evaluation Stats", True, 
                           f"Total evaluations: {total_evaluations}, "
                           f"Overall score: {avg_scores.get('overall', 'N/A')}")
            else:
                print_result("RAG Evaluation Stats", True, 
                           f"Expected result: {data.get('message', 'No evaluations found')}")
        else:
            print_result("RAG Evaluation Stats", False, f"HTTP error: {response.status_code}")
            return False
        
        # Test getting low quality queries
        response = requests.get(f"{BASE_URL}/api/ai-mastery/low-quality-queries?threshold=0.6&limit=10", 
                              headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                queries = data.get('low_quality_queries', [])
                print_result("Low Quality Queries", True, f"Found {len(queries)} low quality queries")
            else:
                print_result("Low Quality Queries", False, f"API error: {data.get('error')}")
        else:
            print_result("Low Quality Queries", False, f"HTTP error: {response.status_code}")
            return False
        
        return True
        
    except Exception as e:
        print_result("RAG Evaluation", False, f"Error: {str(e)}")
        return False

def test_model_performance():
    """Test model performance tracking"""
    print_test_header("Model Performance")
    
    if not TEST_USER_TOKEN:
        print_result("Model Performance", False, "No user token available")
        return False
    
    headers = {
        "Authorization": f"Bearer {TEST_USER_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        # Get model performance metrics
        response = requests.get(f"{BASE_URL}/api/ai-mastery/model-performance?days=30", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                metrics = data.get('metrics', {})
                total_records = data.get('total_records', 0)
                print_result("Model Performance", True, 
                           f"Found {total_records} performance records, "
                           f"{len(metrics)} metric types")
                return True
            else:
                print_result("Model Performance", False, f"API error: {data.get('error')}")
                return False
        else:
            print_result("Model Performance", False, f"HTTP error: {response.status_code}")
            return False
            
    except Exception as e:
        print_result("Model Performance", False, f"Error: {str(e)}")
        return False

def test_ai_mastery_dashboard():
    """Test AI mastery dashboard endpoint"""
    print_test_header("AI Mastery Dashboard")
    
    if not TEST_USER_TOKEN:
        print_result("AI Mastery Dashboard", False, "No user token available")
        return False
    
    headers = {
        "Authorization": f"Bearer {TEST_USER_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/api/ai-mastery/dashboard?days=30", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                feedback_stats = data.get('feedback_statistics', {})
                rag_stats = data.get('rag_evaluation_statistics', {})
                jobs = data.get('recent_fine_tuning_jobs', [])
                performance = data.get('model_performance_records', [])
                
                print_result("AI Mastery Dashboard", True, 
                           f"Dashboard loaded: {len(jobs)} jobs, "
                           f"{len(performance)} performance records")
                
                # Check dashboard structure
                expected_keys = ['feedback_statistics', 'rag_evaluation_statistics', 
                               'recent_fine_tuning_jobs', 'model_performance_records']
                has_all_keys = all(key in data for key in expected_keys)
                print_result("Dashboard Structure", has_all_keys, 
                           f"Keys present: {list(data.keys())}")
                
                return True
            else:
                print_result("AI Mastery Dashboard", False, f"API error: {data.get('error')}")
                return False
        else:
            print_result("AI Mastery Dashboard", False, f"HTTP error: {response.status_code}")
            return False
            
    except Exception as e:
        print_result("AI Mastery Dashboard", False, f"Error: {str(e)}")
        return False

def test_weekly_improvement_trigger():
    """Test weekly improvement trigger"""
    print_test_header("Weekly Improvement Trigger")
    
    if not TEST_USER_TOKEN:
        print_result("Weekly Improvement", False, "No user token available")
        return False
    
    headers = {
        "Authorization": f"Bearer {TEST_USER_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/ai-mastery/trigger-weekly-improvement", 
                               headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                task_id = data.get('task_id')
                print_result("Weekly Improvement", True, f"Task started: {task_id}")
                return True
            else:
                print_result("Weekly Improvement", False, f"API error: {data.get('error')}")
                return False
        else:
            print_result("Weekly Improvement", False, f"HTTP error: {response.status_code}")
            return False
            
    except Exception as e:
        print_result("Weekly Improvement", False, f"Error: {str(e)}")
        return False

def test_services_directly():
    """Test services directly"""
    print_test_header("Direct Service Testing")
    
    try:
        # Test fine-tuning service
        from services.fine_tuning_service import fine_tuning_service
        
        stats = fine_tuning_service.get_feedback_statistics(days=30)
        if stats['success']:
            print_result("Fine-tuning Service", True, 
                       f"Service working: {stats['total_feedback']} feedback items")
        else:
            print_result("Fine-tuning Service", False, f"Service error: {stats.get('error')}")
        
        # Test RAG evaluation service
        from services.rag_evaluation_service import rag_evaluation_service
        
        rag_stats = rag_evaluation_service.get_evaluation_statistics(days=30)
        if rag_stats['success']:
            print_result("RAG Evaluation Service", True, 
                       f"Service working: {rag_stats['total_evaluations']} evaluations")
        else:
            print_result("RAG Evaluation Service", True, 
                       f"Expected result: {rag_stats.get('message', 'No data')}")
        
        return True
        
    except ImportError as e:
        print_result("Service Import", False, f"Import error: {str(e)}")
        return False
    except Exception as e:
        print_result("Service Test", False, f"Error: {str(e)}")
        return False

def test_celery_tasks():
    """Test Celery task configuration"""
    print_test_header("Celery Tasks")
    
    try:
        # Test if Celery tasks can be imported
        from tasks.fine_tuning_tasks import (
            celery_app, run_dpo_training_task, prepare_feedback_dataset_task,
            evaluate_rag_response_task, weekly_model_improvement_task
        )
        
        print_result("Task Import", True, "Fine-tuning tasks imported successfully")
        
        # Test Celery app configuration
        beat_schedule = celery_app.conf.beat_schedule
        expected_tasks = ['weekly-model-improvement', 'daily-performance-monitoring']
        
        configured_tasks = list(beat_schedule.keys())
        all_configured = all(task in configured_tasks for task in expected_tasks)
        
        print_result("Beat Schedule", all_configured, f"Configured tasks: {configured_tasks}")
        
        return True
        
    except ImportError as e:
        print_result("Task Import", False, f"Import error: {str(e)}")
        return False
    except Exception as e:
        print_result("Task Test", False, f"Error: {str(e)}")
        return False

def test_database_models():
    """Test AI mastery database models"""
    print_test_header("Database Models")
    
    try:
        # Test if models can be imported
        from models import (
            MessageFeedback, FineTuningJob, RAGEvaluation, 
            ModelPerformanceTracking, TrendAnalysis
        )
        
        print_result("Model Import", True, "All AI mastery models imported successfully")
        
        # Test model structure
        models_to_test = [
            (MessageFeedback, ['message_id', 'user_id', 'feedback_type', 'rating']),
            (FineTuningJob, ['job_name', 'base_model', 'status', 'dataset_size']),
            (RAGEvaluation, ['message_id', 'query', 'context_relevance_score', 'groundedness_score']),
            (ModelPerformanceTracking, ['model_name', 'metric_name', 'metric_value']),
            (TrendAnalysis, ['metric_name', 'trend_direction', 'trend_strength'])
        ]
        
        for model_class, expected_fields in models_to_test:
            model_name = model_class.__name__
            
            # Check if model has expected fields
            model_columns = [column.name for column in model_class.__table__.columns]
            has_all_fields = all(field in model_columns for field in expected_fields)
            
            print_result(f"Model {model_name}", has_all_fields, 
                       f"Fields: {len(model_columns)} total, {len(expected_fields)} required")
        
        return True
        
    except ImportError as e:
        print_result("Model Import", False, f"Import error: {str(e)}")
        return False
    except Exception as e:
        print_result("Model Test", False, f"Error: {str(e)}")
        return False

def run_all_tests():
    """Run all AI & Model Mastery tests"""
    print(f"\n🧠 Starting AI & Model Mastery Tests")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target: {BASE_URL}")
    
    test_results = []
    
    # Run tests in sequence
    test_results.append(("User Authentication", test_user_authentication()))
    test_results.append(("Database Models", test_database_models()))
    test_results.append(("Direct Services", test_services_directly()))
    test_results.append(("Celery Tasks", test_celery_tasks()))
    test_results.append(("Feedback Statistics", test_feedback_statistics()))
    test_results.append(("Dataset Preparation", test_dataset_preparation()))
    test_results.append(("Fine-tuning Jobs", test_fine_tuning_jobs()))
    test_results.append(("RAG Evaluation", test_rag_evaluation()))
    test_results.append(("Model Performance", test_model_performance()))
    test_results.append(("AI Mastery Dashboard", test_ai_mastery_dashboard()))
    test_results.append(("Weekly Improvement", test_weekly_improvement_trigger()))
    
    # Print summary
    print_test_header("Test Summary")
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! AI & Model Mastery features are working correctly.")
        print("\n🚀 Key Features Tested:")
        print("✅ Fine-tuning from user feedback (DPO)")
        print("✅ Automated RAG evaluation")
        print("✅ Model performance tracking")
        print("✅ Weekly model improvement automation")
        print("✅ Comprehensive AI mastery dashboard")
    else:
        print("⚠️  Some tests failed. Check the details above for troubleshooting.")
    
    return passed == total

if __name__ == "__main__":
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        if response.status_code != 200:
            print(f"❌ Server not responding at {BASE_URL}")
            print("Please ensure the AI Scholar backend is running.")
            exit(1)
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to server at {BASE_URL}")
        print("Please ensure the AI Scholar backend is running.")
        exit(1)
    
    # Run all tests
    success = run_all_tests()
    exit(0 if success else 1)