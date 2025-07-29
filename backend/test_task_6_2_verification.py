"""
Verification script for Task 6.2: Build trend analysis and comparative reporting
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import SessionLocal, Document, DocumentTag, init_db
from services.trend_analyzer import trend_analyzer

async def verify_trend_analyzer_implementation():
    """Verify that TrendAnalyzer is properly implemented"""
    print("=== Verifying TrendAnalyzer Implementation ===")
    
    # Check if TrendAnalyzer class exists and has required methods
    required_methods = [
        'analyze_document_collection_trends',
        'compare_documents',
        '_analyze_tag_trends',
        '_analyze_temporal_trends',
        '_analyze_topic_evolution',
        '_analyze_complexity_trends',
        '_analyze_domain_trends',
        '_generate_trend_insights',
        '_compare_document_tags',
        '_compare_document_complexity',
        '_compare_document_domains',
        '_compare_document_topics',
        '_compare_document_metadata',
        '_calculate_overall_similarity',
        '_generate_comparison_insights'
    ]
    
    print("1. Checking TrendAnalyzer class and methods...")
    
    for method in required_methods:
        if hasattr(trend_analyzer, method):
            print(f"   ✓ {method}")
        else:
            print(f"   ✗ {method} - MISSING")
            return False
    
    # Check initialization parameters
    print("\n2. Checking initialization parameters...")
    
    expected_attributes = [
        'min_documents_for_trend',
        'trend_confidence_threshold',
        'comparison_similarity_threshold'
    ]
    
    for attr in expected_attributes:
        if hasattr(trend_analyzer, attr):
            value = getattr(trend_analyzer, attr)
            print(f"   ✓ {attr}: {value}")
        else:
            print(f"   ✗ {attr} - MISSING")
            return False
    
    print("\n3. Testing basic functionality...")
    
    db = SessionLocal()
    
    try:
        # Test with empty database (should handle gracefully)
        result = await trend_analyzer.analyze_document_collection_trends(
            user_id="test_user",
            db=db,
            time_range_days=30
        )
        
        if result.get('status') == 'insufficient_data':
            print("   ✓ Handles insufficient data correctly")
        else:
            print(f"   ✗ Unexpected result for insufficient data: {result.get('status')}")
            return False
        
        # Test document comparison with invalid IDs (should raise error)
        try:
            await trend_analyzer.compare_documents(
                document_ids=["invalid1"],
                db=db
            )
            print("   ✗ Should have raised error for insufficient documents")
            return False
        except ValueError as e:
            if "Need at least 2 documents" in str(e):
                print("   ✓ Correctly validates minimum document count")
            else:
                print(f"   ✗ Unexpected error: {str(e)}")
                return False
        
    except Exception as e:
        print(f"   ✗ Error during basic functionality test: {str(e)}")
        return False
    finally:
        db.close()
    
    print("\n✓ TrendAnalyzer implementation verification PASSED")
    return True

async def verify_trend_analysis_functionality():
    """Verify trend analysis functionality with sample data"""
    print("\n=== Verifying Trend Analysis Functionality ===")
    
    db = SessionLocal()
    
    try:
        # Create minimal sample data for testing
        user_id = "verify_user"
        base_time = datetime.now() - timedelta(days=10)
        
        # Create sample documents
        sample_docs = []
        for i in range(4):  # Minimum required for trend analysis
            doc_id = f"verify_doc_{i+1}"
            
            # Check if document already exists
            existing_doc = db.query(Document).filter(Document.id == doc_id).first()
            if not existing_doc:
                document = Document(
                    id=doc_id,
                    user_id=user_id,
                    name=f"Test Document {i+1}",
                    file_path=f"/tmp/test_doc_{i+1}.pdf",
                    content_type="application/pdf",
                    size=10000 + i * 5000,
                    status="completed",
                    chunks_count=5,
                    embeddings_count=5,
                    created_at=base_time + timedelta(days=i*2)
                )
                db.add(document)
                sample_docs.append(document)
        
        db.commit()
        
        # Create sample tags
        tag_types = ["topic", "domain", "complexity"]
        tag_names = {
            "topic": ["machine_learning", "data_science", "artificial_intelligence"],
            "domain": ["computer_science", "technology"],
            "complexity": ["complexity_intermediate", "complexity_advanced"]
        }
        
        for i, doc_id in enumerate([f"verify_doc_{j+1}" for j in range(4)]):
            # Check if tags already exist
            existing_tags = db.query(DocumentTag).filter(
                DocumentTag.document_id == doc_id
            ).first()
            
            if not existing_tags:
                for tag_type in tag_types:
                    tag_name = tag_names[tag_type][i % len(tag_names[tag_type])]
                    tag = DocumentTag(
                        document_id=doc_id,
                        tag_name=tag_name,
                        tag_type=tag_type,
                        confidence_score=0.8 + (i * 0.05),
                        generated_by="test"
                    )
                    db.add(tag)
        
        db.commit()
        
        print("1. Testing document collection trend analysis...")
        
        # Test trend analysis
        trend_result = await trend_analyzer.analyze_document_collection_trends(
            user_id=user_id,
            db=db,
            time_range_days=30
        )
        
        # Verify trend analysis structure
        required_keys = ['status', 'document_count', 'trends', 'insights', 'analysis_period']
        for key in required_keys:
            if key in trend_result:
                print(f"   ✓ {key}")
            else:
                print(f"   ✗ {key} - MISSING")
                return False
        
        if trend_result['status'] == 'success':
            trends = trend_result['trends']
            required_trend_types = ['tag_trends', 'temporal_trends', 'topic_evolution', 'complexity_trends', 'domain_trends']
            
            for trend_type in required_trend_types:
                if trend_type in trends:
                    print(f"   ✓ {trend_type}")
                else:
                    print(f"   ✗ {trend_type} - MISSING")
                    return False
        
        print("\n2. Testing document comparison...")
        
        # Test document comparison
        doc_ids = [f"verify_doc_{i+1}" for i in range(3)]
        comparison_result = await trend_analyzer.compare_documents(
            document_ids=doc_ids,
            db=db
        )
        
        # Verify comparison structure
        required_comp_keys = ['documents', 'comparisons', 'overall_similarity', 'insights']
        for key in required_comp_keys:
            if key in comparison_result:
                print(f"   ✓ {key}")
            else:
                print(f"   ✗ {key} - MISSING")
                return False
        
        # Verify comparison types
        comparisons = comparison_result['comparisons']
        required_comp_types = ['tag_comparison', 'complexity_comparison', 'domain_comparison', 'topic_comparison', 'metadata_comparison']
        
        for comp_type in required_comp_types:
            if comp_type in comparisons:
                print(f"   ✓ {comp_type}")
            else:
                print(f"   ✗ {comp_type} - MISSING")
                return False
        
        print("\n3. Testing specific comparison aspects...")
        
        # Test with specific aspects
        specific_result = await trend_analyzer.compare_documents(
            document_ids=doc_ids[:2],
            db=db,
            comparison_aspects=["tags", "complexity"]
        )
        
        if len(specific_result['comparisons']) == 2:  # Only requested aspects
            print("   ✓ Specific aspect filtering works")
        else:
            print(f"   ✗ Expected 2 comparison aspects, got {len(specific_result['comparisons'])}")
            return False
        
        print("\n✓ Trend analysis functionality verification PASSED")
        return True
        
    except Exception as e:
        print(f"   ✗ Error during functionality verification: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

async def verify_error_handling():
    """Verify error handling in trend analysis"""
    print("\n=== Verifying Error Handling ===")
    
    db = SessionLocal()
    
    try:
        print("1. Testing insufficient documents error...")
        
        result = await trend_analyzer.analyze_document_collection_trends(
            user_id="nonexistent_user",
            db=db,
            time_range_days=30
        )
        
        if result.get('status') == 'insufficient_data':
            print("   ✓ Handles insufficient documents correctly")
        else:
            print(f"   ✗ Expected 'insufficient_data', got '{result.get('status')}'")
            return False
        
        print("\n2. Testing invalid document comparison...")
        
        try:
            await trend_analyzer.compare_documents(
                document_ids=["invalid1", "invalid2"],
                db=db
            )
            print("   ✗ Should have raised error for invalid documents")
            return False
        except ValueError as e:
            if "Documents not found" in str(e):
                print("   ✓ Correctly handles invalid document IDs")
            else:
                print(f"   ✗ Unexpected error: {str(e)}")
                return False
        
        print("\n3. Testing insufficient documents for comparison...")
        
        try:
            await trend_analyzer.compare_documents(
                document_ids=["single_doc"],
                db=db
            )
            print("   ✗ Should have raised error for single document")
            return False
        except ValueError as e:
            if "Need at least 2 documents" in str(e):
                print("   ✓ Correctly validates minimum document count")
            else:
                print(f"   ✗ Unexpected error: {str(e)}")
                return False
        
        print("\n✓ Error handling verification PASSED")
        return True
        
    except Exception as e:
        print(f"   ✗ Error during error handling verification: {str(e)}")
        return False
    finally:
        db.close()

async def verify_requirements_compliance():
    """Verify compliance with task requirements"""
    print("\n=== Verifying Requirements Compliance ===")
    
    # Requirements from task:
    # - Implement TrendAnalyzer for document collection analysis
    # - Create comparative analysis between documents  
    # - Add trend detection across document metadata
    # - Test trend analysis accuracy and insights
    # - Requirements: 5.2, 5.3
    
    requirements_check = {
        "TrendAnalyzer for document collection analysis": False,
        "Comparative analysis between documents": False,
        "Trend detection across document metadata": False,
        "Test trend analysis accuracy and insights": False
    }
    
    print("1. Checking TrendAnalyzer for document collection analysis...")
    if hasattr(trend_analyzer, 'analyze_document_collection_trends'):
        requirements_check["TrendAnalyzer for document collection analysis"] = True
        print("   ✓ TrendAnalyzer.analyze_document_collection_trends() implemented")
    else:
        print("   ✗ TrendAnalyzer.analyze_document_collection_trends() missing")
    
    print("\n2. Checking comparative analysis between documents...")
    if hasattr(trend_analyzer, 'compare_documents'):
        requirements_check["Comparative analysis between documents"] = True
        print("   ✓ TrendAnalyzer.compare_documents() implemented")
    else:
        print("   ✗ TrendAnalyzer.compare_documents() missing")
    
    print("\n3. Checking trend detection across document metadata...")
    trend_methods = [
        '_analyze_tag_trends',
        '_analyze_temporal_trends', 
        '_analyze_topic_evolution',
        '_analyze_complexity_trends',
        '_analyze_domain_trends'
    ]
    
    all_trend_methods_exist = all(hasattr(trend_analyzer, method) for method in trend_methods)
    if all_trend_methods_exist:
        requirements_check["Trend detection across document metadata"] = True
        print("   ✓ All trend detection methods implemented")
    else:
        print("   ✗ Some trend detection methods missing")
    
    print("\n4. Checking test implementation...")
    test_files = [
        "test_trend_analysis_demo.py",
        "test_task_6_2_verification.py",
        "tests/test_trend_analyzer.py"
    ]
    
    test_files_exist = all(os.path.exists(f) for f in test_files)
    if test_files_exist:
        requirements_check["Test trend analysis accuracy and insights"] = True
        print("   ✓ Test files implemented")
    else:
        print("   ✗ Some test files missing")
    
    # Overall compliance check
    all_requirements_met = all(requirements_check.values())
    
    print(f"\n=== Requirements Compliance Summary ===")
    for requirement, met in requirements_check.items():
        status = "✓" if met else "✗"
        print(f"{status} {requirement}")
    
    if all_requirements_met:
        print("\n✓ ALL REQUIREMENTS MET")
        return True
    else:
        print("\n✗ SOME REQUIREMENTS NOT MET")
        return False

async def main():
    """Main verification function"""
    print("Starting Task 6.2 Verification...")
    print("Task: Build trend analysis and comparative reporting")
    
    # Initialize database
    await init_db()
    
    # Run all verification tests
    tests = [
        verify_trend_analyzer_implementation,
        verify_trend_analysis_functionality,
        verify_error_handling,
        verify_requirements_compliance
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"Error in {test.__name__}: {str(e)}")
            results.append(False)
    
    # Final summary
    print(f"\n{'='*50}")
    print("VERIFICATION SUMMARY")
    print(f"{'='*50}")
    
    test_names = [
        "TrendAnalyzer Implementation",
        "Trend Analysis Functionality", 
        "Error Handling",
        "Requirements Compliance"
    ]
    
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "PASSED" if result else "FAILED"
        print(f"{i+1}. {name}: {status}")
    
    overall_success = all(results)
    print(f"\nOVERALL RESULT: {'SUCCESS' if overall_success else 'FAILURE'}")
    
    if overall_success:
        print("\n✓ Task 6.2 implementation is complete and working correctly!")
        print("✓ TrendAnalyzer for document collection analysis implemented")
        print("✓ Comparative analysis between documents implemented")
        print("✓ Trend detection across document metadata implemented")
        print("✓ Tests for trend analysis accuracy and insights implemented")
    else:
        print("\n✗ Task 6.2 implementation has issues that need to be addressed")
    
    return overall_success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)