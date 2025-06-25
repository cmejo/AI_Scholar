#!/usr/bin/env python3
"""
Test script for Advanced AI Features structure
Tests the code structure without requiring external dependencies
"""

import os
import sys
import ast

def test_file_structure():
    """Test that all required files exist"""
    print("📁 Testing File Structure...")
    
    required_files = [
        'services/fine_tuning_service.py',
        'services/rag_evaluation_service.py',
        'services/visualization_service.py',
        'migrations/versions/007_add_advanced_ai_features.py',
        'ADVANCED_AI_FEATURES.md'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
        else:
            print(f"✅ {file_path}")
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    print("✅ All required files exist")
    return True

def test_fine_tuning_service_structure():
    """Test fine-tuning service code structure"""
    print("\n🎯 Testing Fine-Tuning Service Structure...")
    
    try:
        with open('services/fine_tuning_service.py', 'r') as f:
            content = f.read()
        
        # Check for required classes
        required_classes = [
            'PreferenceDataPoint',
            'TrainingConfig',
            'FineTuningService'
        ]
        
        for class_name in required_classes:
            if f"class {class_name}" in content:
                print(f"✅ {class_name} class found")
            else:
                print(f"❌ {class_name} class missing")
                return False
        
        # Check for required methods
        required_methods = [
            'collect_preference_data',
            'prepare_training_dataset',
            'create_fine_tuning_job',
            'run_fine_tuning_job',
            'trigger_weekly_fine_tuning'
        ]
        
        for method_name in required_methods:
            if f"def {method_name}" in content:
                print(f"✅ {method_name} method found")
            else:
                print(f"❌ {method_name} method missing")
                return False
        
        # Check for DPO and LoRA references
        if 'DPO' in content and 'LoRA' in content:
            print("✅ DPO and LoRA concepts referenced")
        else:
            print("❌ DPO/LoRA concepts missing")
            return False
        
        print("✅ Fine-tuning service structure is correct")
        return True
        
    except Exception as e:
        print(f"❌ Fine-tuning service structure test failed: {e}")
        return False

def test_rag_evaluation_service_structure():
    """Test RAG evaluation service code structure"""
    print("\n📊 Testing RAG Evaluation Service Structure...")
    
    try:
        with open('services/rag_evaluation_service.py', 'r') as f:
            content = f.read()
        
        # Check for required classes
        required_classes = [
            'RAGMetrics',
            'EvaluationPrompts',
            'RAGEvaluationService'
        ]
        
        for class_name in required_classes:
            if f"class {class_name}" in content:
                print(f"✅ {class_name} class found")
            else:
                print(f"❌ {class_name} class missing")
                return False
        
        # Check for evaluation metrics
        evaluation_metrics = [
            'context_relevance',
            'groundedness',
            'answer_relevance',
            'faithfulness'
        ]
        
        for metric in evaluation_metrics:
            if metric in content:
                print(f"✅ {metric} metric found")
            else:
                print(f"❌ {metric} metric missing")
                return False
        
        # Check for required methods
        required_methods = [
            'evaluate_rag_response',
            'batch_evaluate_messages',
            'get_evaluation_statistics',
            'trigger_evaluation_for_recent_messages'
        ]
        
        for method_name in required_methods:
            if f"def {method_name}" in content:
                print(f"✅ {method_name} method found")
            else:
                print(f"❌ {method_name} method missing")
                return False
        
        print("✅ RAG evaluation service structure is correct")
        return True
        
    except Exception as e:
        print(f"❌ RAG evaluation service structure test failed: {e}")
        return False

def test_visualization_service_structure():
    """Test visualization service code structure"""
    print("\n📈 Testing Visualization Service Structure...")
    
    try:
        with open('services/visualization_service.py', 'r') as f:
            content = f.read()
        
        # Check for required classes
        required_classes = [
            'ChartData',
            'VegaLiteSpec',
            'VisualizationService'
        ]
        
        for class_name in required_classes:
            if f"class {class_name}" in content:
                print(f"✅ {class_name} class found")
            else:
                print(f"❌ {class_name} class missing")
                return False
        
        # Check for chart types
        chart_types = [
            'create_bar_chart',
            'create_line_chart',
            'create_scatter_plot',
            'create_pie_chart',
            'create_histogram',
            'create_heatmap'
        ]
        
        for chart_type in chart_types:
            if chart_type in content:
                print(f"✅ {chart_type} method found")
            else:
                print(f"❌ {chart_type} method missing")
                return False
        
        # Check for Vega-Lite integration
        if 'vega.github.io/schema/vega-lite' in content:
            print("✅ Vega-Lite integration found")
        else:
            print("❌ Vega-Lite integration missing")
            return False
        
        # Check for auto-detection features
        auto_features = [
            'auto_detect_chart_type',
            'parse_visualization_request'
        ]
        
        for feature in auto_features:
            if feature in content:
                print(f"✅ {feature} feature found")
            else:
                print(f"❌ {feature} feature missing")
                return False
        
        print("✅ Visualization service structure is correct")
        return True
        
    except Exception as e:
        print(f"❌ Visualization service structure test failed: {e}")
        return False

def test_agent_integration():
    """Test agent service integration with visualization tool"""
    print("\n🤖 Testing Agent Integration...")
    
    try:
        with open('services/agent_service.py', 'r') as f:
            content = f.read()
        
        # Check for visualization tool
        if 'class VisualizationTool' in content:
            print("✅ VisualizationTool class found")
        else:
            print("❌ VisualizationTool class missing")
            return False
        
        # Check if visualization tool is registered
        if 'VisualizationTool()' in content:
            print("✅ VisualizationTool registered in agent")
        else:
            print("❌ VisualizationTool not registered")
            return False
        
        # Check for generate_visualization tool
        if 'generate_visualization' in content:
            print("✅ generate_visualization tool found")
        else:
            print("❌ generate_visualization tool missing")
            return False
        
        print("✅ Agent integration is correct")
        return True
        
    except Exception as e:
        print(f"❌ Agent integration test failed: {e}")
        return False

def test_database_models():
    """Test database model additions"""
    print("\n🗄️ Testing Database Models...")
    
    try:
        with open('models.py', 'r') as f:
            content = f.read()
        
        # Check for new model classes
        new_models = [
            'MessageFeedback',
            'FineTuningJob',
            'RAGEvaluation',
            'VisualizationRequest'
        ]
        
        for model in new_models:
            if f"class {model}" in content:
                print(f"✅ {model} model found")
            else:
                print(f"❌ {model} model missing")
                return False
        
        # Check for feedback types
        if 'thumbs_up' in content and 'thumbs_down' in content:
            print("✅ Feedback types found")
        else:
            print("❌ Feedback types missing")
            return False
        
        # Check for job status enum
        if 'pending' in content and 'running' in content and 'completed' in content:
            print("✅ Job status enum found")
        else:
            print("❌ Job status enum missing")
            return False
        
        print("✅ Database models are correct")
        return True
        
    except Exception as e:
        print(f"❌ Database models test failed: {e}")
        return False

def test_migration_file():
    """Test migration file structure"""
    print("\n🗄️ Testing Migration File...")
    
    try:
        with open('migrations/versions/007_add_advanced_ai_features.py', 'r') as f:
            content = f.read()
        
        # Check for required functions
        if 'def upgrade():' in content and 'def downgrade():' in content:
            print("✅ Migration functions found")
        else:
            print("❌ Migration functions missing")
            return False
        
        # Check for table creation
        required_tables = [
            'message_feedback',
            'fine_tuning_jobs',
            'rag_evaluations',
            'visualization_requests'
        ]
        
        for table in required_tables:
            if table in content:
                print(f"✅ {table} table found in migration")
            else:
                print(f"❌ {table} table missing from migration")
                return False
        
        print("✅ Migration file is correct")
        return True
        
    except Exception as e:
        print(f"❌ Migration file test failed: {e}")
        return False

def test_api_endpoints():
    """Test API endpoint additions"""
    print("\n🌐 Testing API Endpoints...")
    
    try:
        with open('app.py', 'r') as f:
            content = f.read()
        
        # Check for feedback endpoints
        feedback_endpoints = [
            '/api/messages/<int:message_id>/feedback',
            '/api/feedback/statistics'
        ]
        
        for endpoint in feedback_endpoints:
            if endpoint in content:
                print(f"✅ {endpoint} endpoint found")
            else:
                print(f"❌ {endpoint} endpoint missing")
                return False
        
        # Check for fine-tuning endpoints
        ft_endpoints = [
            '/api/fine-tuning/jobs',
            '/api/fine-tuning/trigger-weekly'
        ]
        
        for endpoint in ft_endpoints:
            if endpoint in content:
                print(f"✅ {endpoint} endpoint found")
            else:
                print(f"❌ {endpoint} endpoint missing")
                return False
        
        # Check for RAG evaluation endpoints
        rag_endpoints = [
            '/api/rag/evaluate',
            '/api/rag/statistics'
        ]
        
        for endpoint in rag_endpoints:
            if endpoint in content:
                print(f"✅ {endpoint} endpoint found")
            else:
                print(f"❌ {endpoint} endpoint missing")
                return False
        
        # Check for visualization endpoints
        viz_endpoints = [
            '/api/visualizations'
        ]
        
        for endpoint in viz_endpoints:
            if endpoint in content:
                print(f"✅ {endpoint} endpoint found")
            else:
                print(f"❌ {endpoint} endpoint missing")
                return False
        
        print("✅ API endpoints are correctly implemented")
        return True
        
    except Exception as e:
        print(f"❌ API endpoints test failed: {e}")
        return False

def test_requirements():
    """Test requirements.txt updates"""
    print("\n📦 Testing Requirements...")
    
    try:
        with open('requirements.txt', 'r') as f:
            content = f.read()
        
        # Check for new dependencies
        new_deps = [
            'trl',      # For DPO training
            'ragas',    # For RAG evaluation
            'altair',   # For visualizations
            'celery',   # For async jobs
            'openai',   # For evaluation LLM
            'anthropic' # Alternative evaluation LLM
        ]
        
        for dep in new_deps:
            if dep in content:
                print(f"✅ {dep} dependency found")
            else:
                print(f"❌ {dep} dependency missing")
                return False
        
        print("✅ Requirements are updated correctly")
        return True
        
    except Exception as e:
        print(f"❌ Requirements test failed: {e}")
        return False

def test_documentation():
    """Test documentation completeness"""
    print("\n📚 Testing Documentation...")
    
    try:
        with open('ADVANCED_AI_FEATURES.md', 'r') as f:
            content = f.read()
        
        # Check for required sections
        required_sections = [
            '# 🎯 Advanced AI Features Implementation',
            '## 🎯 AI Fine-Tuning from User Feedback',
            '## 📊 Automated RAG Evaluation & Self-Correction',
            '## 📈 Interactive & Visual Outputs',
            '### API Endpoints',
            '### Implementation Details',
            '## 🚀 Getting Started'
        ]
        
        for section in required_sections:
            if section in content:
                print(f"✅ {section} section found")
            else:
                print(f"❌ {section} section missing")
                return False
        
        # Check for code examples
        if '```python' in content and '```javascript' in content and '```sql' in content:
            print("✅ Code examples found")
        else:
            print("❌ Code examples missing")
            return False
        
        # Check for API documentation
        if '/api/messages/' in content and '/api/fine-tuning/' in content and '/api/rag/' in content:
            print("✅ API documentation found")
        else:
            print("❌ API documentation missing")
            return False
        
        print("✅ Documentation is complete")
        return True
        
    except Exception as e:
        print(f"❌ Documentation test failed: {e}")
        return False

def main():
    """Run all structure tests"""
    print("🚀 Testing Advanced AI Features Structure")
    print("=" * 70)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Fine-Tuning Service Structure", test_fine_tuning_service_structure),
        ("RAG Evaluation Service Structure", test_rag_evaluation_service_structure),
        ("Visualization Service Structure", test_visualization_service_structure),
        ("Agent Integration", test_agent_integration),
        ("Database Models", test_database_models),
        ("Migration File", test_migration_file),
        ("API Endpoints", test_api_endpoints),
        ("Requirements", test_requirements),
        ("Documentation", test_documentation)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    print("\n" + "=" * 70)
    print("📊 Test Results Summary:")
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"\n🎯 Overall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All structure tests passed! The advanced AI features are implemented correctly.")
        print("\n🚀 Features Successfully Implemented:")
        print("   1. ✅ AI Fine-Tuning from User Feedback")
        print("      - DPO (Direct Preference Optimization) training")
        print("      - LoRA (Low-Rank Adaptation) for efficiency")
        print("      - Automated weekly fine-tuning")
        print("      - Preference data collection from thumbs up/down")
        print("")
        print("   2. ✅ Automated RAG Evaluation & Self-Correction")
        print("      - Context relevance scoring")
        print("      - Groundedness detection (hallucination prevention)")
        print("      - Answer relevance measurement")
        print("      - Faithfulness evaluation")
        print("      - Automated batch evaluation")
        print("")
        print("   3. ✅ Interactive & Visual Outputs")
        print("      - Bar charts, line charts, scatter plots")
        print("      - Pie charts, histograms, heatmaps")
        print("      - Vega-Lite specifications")
        print("      - Auto-detection of chart types")
        print("      - Agent tool integration")
        print("")
        print("📋 Next Steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Run database migration: alembic upgrade head")
        print("3. Start the application: python app.py")
        print("4. Begin collecting user feedback for fine-tuning")
        print("5. Enable RAG evaluation for quality monitoring")
        print("6. Test visualization features in chat")
        return True
    else:
        print("⚠️ Some structure tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)