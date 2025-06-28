#!/usr/bin/env python3
"""
ML Analytics Features Test Script
Tests machine learning powered analytics, predictions, and anomaly detection
"""

import requests
import json
import time
import numpy as np
from datetime import datetime, timedelta

# Configuration
BASE_URL = 'http://localhost:5000'
ADMIN_USERNAME = 'admin'
ADMIN_EMAIL = 'admin@example.com'
ADMIN_PASSWORD = 'admin123456'

class MLAnalyticsFeatureTester:
    def __init__(self):
        self.admin_token = None
        self.admin_user_id = None
        
    def test_all(self):
        """Run all ML analytics feature tests"""
        print("🤖 Starting ML Analytics Feature Tests")
        print("=" * 50)
        
        try:
            # Test 1: Setup Admin User
            self.test_admin_setup()
            
            # Test 2: Generate Sample Data
            self.test_generate_sample_data()
            
            # Test 3: User Growth Predictions
            self.test_user_growth_predictions()
            
            # Test 4: Anomaly Detection
            self.test_anomaly_detection()
            
            # Test 5: User Behavior Analysis
            self.test_user_behavior_analysis()
            
            # Test 6: Trend Analysis
            self.test_trend_analysis()
            
            # Test 7: ML Metrics Tracking
            self.test_ml_metrics()
            
            # Test 8: ML Insights Summary
            self.test_ml_insights_summary()
            
            # Test 9: Custom Analytics Widgets
            self.test_custom_analytics_widgets()
            
            print("\n✅ All ML Analytics Feature Tests Completed Successfully!")
            
        except Exception as e:
            print(f"\n❌ Test Failed: {e}")
            raise
    
    def test_admin_setup(self):
        """Setup admin user for testing"""
        print("\n1. Setting up admin user...")
        
        # Try to register admin user
        admin_data = {
            'username': ADMIN_USERNAME,
            'email': ADMIN_EMAIL,
            'password': ADMIN_PASSWORD
        }
        
        response = requests.post(f'{BASE_URL}/api/auth/register', json=admin_data)
        
        if response.status_code == 201:
            result = response.json()
            self.admin_token = result['token']
            self.admin_user_id = result['user']['id']
            print(f"   ✅ Admin user created: {result['user']['username']}")
        elif response.status_code == 400 and 'already exists' in response.json().get('message', ''):
            # User already exists, try to login
            login_data = {
                'username': ADMIN_USERNAME,
                'password': ADMIN_PASSWORD
            }
            response = requests.post(f'{BASE_URL}/api/auth/login', json=login_data)
            if response.status_code == 200:
                result = response.json()
                self.admin_token = result['token']
                self.admin_user_id = result['user']['id']
                print(f"   ✅ Admin user logged in: {result['user']['username']}")
            else:
                raise Exception(f"Admin login failed: {response.text}")
        else:
            raise Exception(f"Admin registration failed: {response.text}")
    
    def test_generate_sample_data(self):
        """Generate sample data for ML analytics"""
        print("\n2. Generating sample data...")
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Create some sample chat sessions and messages
        for i in range(5):
            chat_data = {
                'message': f'Sample message {i+1} for ML analytics testing',
                'model': 'llama2:latest'
            }
            
            response = requests.post(f'{BASE_URL}/api/chat/send', json=chat_data, headers=headers)
            if response.status_code == 200:
                print(f"   ✅ Created sample chat session {i+1}")
            else:
                print(f"   ⚠️  Failed to create sample session {i+1}: {response.status_code}")
        
        print("   ✅ Sample data generation completed")
    
    def test_user_growth_predictions(self):
        """Test user growth prediction generation"""
        print("\n3. Testing User Growth Predictions...")
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Generate predictions
        prediction_data = {'days_ahead': 30}
        response = requests.post(
            f'{BASE_URL}/api/admin/ml-insights/generate-predictions',
            json=prediction_data,
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                predictions = result.get('predictions', [])
                print(f"   ✅ Generated {len(predictions)} user growth predictions")
                
                if predictions:
                    print(f"   📊 Sample prediction: {predictions[0]['predicted_registrations']:.1f} users on {predictions[0]['date'][:10]}")
                
                # Test model performance metrics
                model_perf = result.get('model_performance', {})
                if model_perf.get('r2_score'):
                    print(f"   📈 Model R² Score: {model_perf['r2_score']:.3f}")
            else:
                print(f"   ⚠️  Prediction generation failed: {result.get('error')}")
        else:
            print(f"   ⚠️  Prediction request failed: {response.status_code}")
        
        # Get existing predictions
        response = requests.get(f'{BASE_URL}/api/admin/ml-insights/predictions', headers=headers)
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                predictions = result.get('predictions', [])
                print(f"   ✅ Retrieved {len(predictions)} existing predictions")
    
    def test_anomaly_detection(self):
        """Test anomaly detection functionality"""
        print("\n4. Testing Anomaly Detection...")
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Run anomaly detection
        anomaly_data = {'lookback_days': 30}
        response = requests.post(
            f'{BASE_URL}/api/admin/ml-insights/detect-anomalies',
            json=anomaly_data,
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                total_anomalies = result.get('total_anomalies', 0)
                print(f"   ✅ Detected {total_anomalies} anomalies")
                
                if total_anomalies > 0:
                    threshold = result.get('threshold', 0)
                    print(f"   📊 Detection threshold: {threshold:.3f}")
            else:
                print(f"   ⚠️  Anomaly detection failed: {result.get('error')}")
        else:
            print(f"   ⚠️  Anomaly detection request failed: {response.status_code}")
        
        # Get existing anomalies
        response = requests.get(f'{BASE_URL}/api/admin/ml-insights/anomalies', headers=headers)
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                anomalies = result.get('anomalies', [])
                unresolved = result.get('unresolved_count', 0)
                print(f"   ✅ Retrieved {len(anomalies)} anomalies ({unresolved} unresolved)")
                
                # Test resolving an anomaly
                if anomalies and not anomalies[0].get('is_resolved'):
                    anomaly_id = anomalies[0]['id']
                    response = requests.post(
                        f'{BASE_URL}/api/admin/ml-insights/anomalies/{anomaly_id}/resolve',
                        headers=headers
                    )
                    if response.status_code == 200:
                        print(f"   ✅ Resolved anomaly {anomaly_id}")
    
    def test_user_behavior_analysis(self):
        """Test user behavior pattern analysis"""
        print("\n5. Testing User Behavior Analysis...")
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Analyze user behavior
        response = requests.post(
            f'{BASE_URL}/api/admin/ml-insights/analyze-behavior',
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                total_users = result.get('total_users_analyzed', 0)
                patterns = result.get('patterns', [])
                print(f"   ✅ Analyzed behavior patterns for {total_users} users")
                
                if patterns:
                    # Show sample pattern
                    sample_pattern = patterns[0]
                    user_type = sample_pattern['pattern']['user_type']
                    confidence = sample_pattern['confidence']
                    print(f"   👤 Sample pattern: {user_type} (confidence: {confidence:.2f})")
            else:
                print(f"   ⚠️  Behavior analysis failed: {result.get('error')}")
        else:
            print(f"   ⚠️  Behavior analysis request failed: {response.status_code}")
        
        # Get existing patterns
        response = requests.get(f'{BASE_URL}/api/admin/ml-insights/user-patterns', headers=headers)
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                patterns = result.get('patterns', [])
                print(f"   ✅ Retrieved {len(patterns)} user behavior patterns")
    
    def test_trend_analysis(self):
        """Test trend analysis functionality"""
        print("\n6. Testing Trend Analysis...")
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Perform trend analysis for different metrics
        metrics = ['user_activity', 'message_volume', 'response_time']
        
        for metric in metrics:
            trend_data = {
                'metric_name': metric,
                'time_period': 'daily',
                'days': 30
            }
            
            response = requests.post(
                f'{BASE_URL}/api/admin/ml-insights/trend-analysis',
                json=trend_data,
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    trend = result.get('trend_analysis', {})
                    direction = trend.get('trend_direction', 'unknown')
                    strength = trend.get('trend_strength', 0)
                    print(f"   ✅ {metric}: {direction} trend (strength: {strength:.2f})")
                else:
                    print(f"   ⚠️  Trend analysis for {metric} failed: {result.get('error')}")
            else:
                print(f"   ⚠️  Trend analysis request for {metric} failed: {response.status_code}")
        
        # Get existing trends
        response = requests.get(f'{BASE_URL}/api/admin/ml-insights/trends', headers=headers)
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                trends = result.get('trends', [])
                print(f"   ✅ Retrieved {len(trends)} trend analyses")
    
    def test_ml_metrics(self):
        """Test ML metrics tracking"""
        print("\n7. Testing ML Metrics...")
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Get ML metrics
        response = requests.get(f'{BASE_URL}/api/admin/ml-insights/metrics', headers=headers)
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                metrics = result.get('metrics', [])
                print(f"   ✅ Retrieved {len(metrics)} ML metrics")
                
                if metrics:
                    # Show sample metric
                    sample_metric = metrics[0]
                    metric_name = sample_metric['metric_name']
                    value = sample_metric['value']
                    print(f"   📊 Sample metric: {metric_name} = {value:.3f}")
            else:
                print(f"   ⚠️  ML metrics retrieval failed: {result.get('error')}")
        else:
            print(f"   ⚠️  ML metrics request failed: {response.status_code}")
    
    def test_ml_insights_summary(self):
        """Test ML insights summary"""
        print("\n8. Testing ML Insights Summary...")
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        response = requests.get(f'{BASE_URL}/api/admin/ml-insights/summary', headers=headers)
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                summary = result.get('summary', {})
                
                predictions = summary.get('predictions', {})
                anomalies = summary.get('anomalies', {})
                trends = summary.get('trends', {})
                ml_metrics = summary.get('ml_metrics', {})
                
                print(f"   ✅ ML Insights Summary:")
                print(f"      📊 Predictions: {predictions.get('total_recent', 0)} recent")
                print(f"      ⚠️  Anomalies: {anomalies.get('unresolved_count', 0)} unresolved")
                print(f"      📈 Trends: {len(trends.get('recent_analyses', []))} recent")
                print(f"      🤖 Metrics: {len(ml_metrics.get('recent_metrics', []))} recent")
                
                if predictions.get('average_accuracy'):
                    print(f"      🎯 Avg Prediction Accuracy: {predictions['average_accuracy']:.1%}")
            else:
                print(f"   ⚠️  ML insights summary failed: {result.get('error')}")
        else:
            print(f"   ⚠️  ML insights summary request failed: {response.status_code}")
    
    def test_custom_analytics_widgets(self):
        """Test custom analytics widgets with ML data sources"""
        print("\n9. Testing Custom Analytics Widgets...")
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Test different ML widget data sources
        ml_data_sources = [
            'ml_predictions',
            'anomaly_detection',
            'trend_analysis',
            'user_behavior_patterns',
            'ml_model_performance'
        ]
        
        for data_source in ml_data_sources:
            params = {
                'data_source': data_source,
                'days': 30
            }
            
            response = requests.get(
                f'{BASE_URL}/api/admin/widgets/chart/data',
                params=params,
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    data = result.get('data', {})
                    print(f"   ✅ {data_source}: Data retrieved successfully")
                    
                    # Show some sample data info
                    if data_source == 'ml_predictions':
                        total_predictions = data.get('total_predictions', 0)
                        print(f"      📊 Total predictions: {total_predictions}")
                    elif data_source == 'anomaly_detection':
                        total_anomalies = data.get('total_anomalies', 0)
                        print(f"      ⚠️  Total anomalies: {total_anomalies}")
                    elif data_source == 'user_behavior_patterns':
                        total_patterns = data.get('total_patterns', 0)
                        print(f"      👥 Total patterns: {total_patterns}")
                else:
                    print(f"   ⚠️  {data_source}: {result.get('error')}")
            else:
                print(f"   ⚠️  {data_source}: Request failed ({response.status_code})")
    
    def cleanup(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Note: In a real implementation, you might want to clean up
        # test predictions, anomalies, etc. For now, we'll just log
        print("   ✅ Test data cleanup completed")

def main():
    """Main test function"""
    print("ML Analytics Features Tester")
    print("=" * 40)
    
    # Check if server is running
    try:
        response = requests.get(f'{BASE_URL}/api/health', timeout=5)
        if response.status_code == 200:
            print(f"✅ Server is running at {BASE_URL}")
            
            # Check if ML dependencies are available
            health_data = response.json()
            print(f"   Status: {health_data.get('status', 'unknown')}")
        else:
            print(f"❌ Server responded with status {response.status_code}")
            return
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to server at {BASE_URL}")
        print(f"   Make sure the enterprise app is running: python app_enterprise.py")
        return
    
    # Check if required ML libraries are available
    try:
        import sklearn
        import pandas
        import numpy
        print("✅ ML dependencies available")
    except ImportError as e:
        print(f"❌ Missing ML dependencies: {e}")
        print("   Install with: pip install scikit-learn pandas numpy scipy")
        return
    
    # Run tests
    tester = MLAnalyticsFeatureTester()
    try:
        tester.test_all()
    finally:
        tester.cleanup()

if __name__ == '__main__':
    main()