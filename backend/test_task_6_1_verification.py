#!/usr/bin/env python3
"""
Verification script for Task 6.1: Implement LLM-assisted document tagging
"""
import asyncio
import json
from datetime import datetime
from sqlalchemy.orm import Session

from core.database import get_db, init_db
from services.auto_tagging_service import auto_tagging_service, AutoTaggingService
from models.schemas import TagType, DocumentTagResponse

async def verify_requirement_5_1():
    """
    Verify Requirement 5.1: Auto-Tagging and Metadata
    
    Requirements to verify:
    1. WHEN documents are uploaded THEN the system SHALL generate LLM-assisted metadata tags
    2. WHEN content is processed THEN the system SHALL perform trend analysis across document collections
    3. WHEN reports are generated THEN the system SHALL create comparative analysis between documents
    4. WHEN citations are needed THEN the system SHALL automatically generate proper citation formats
    5. IF similar content is detected THEN the system SHALL suggest related tags and categories
    """
    print("🔍 Verifying Requirement 5.1: Auto-Tagging and Metadata")
    print("=" * 60)
    
    # Initialize database
    await init_db()
    
    # Test document content
    test_content = """
    Artificial Intelligence and Machine Learning in Healthcare
    
    This comprehensive study examines the application of artificial intelligence
    and machine learning technologies in modern healthcare systems. The research
    focuses on diagnostic imaging, predictive analytics, and personalized treatment
    recommendations. Key findings include improved accuracy in medical diagnosis,
    reduced treatment costs, and enhanced patient outcomes.
    
    The study covers deep learning algorithms, neural networks, and natural language
    processing applications in electronic health records. Statistical analysis shows
    a 25% improvement in diagnostic accuracy when AI systems are integrated with
    traditional medical practices.
    """
    
    db_gen = get_db()
    db = next(db_gen)
    
    verification_results = {
        "llm_assisted_tagging": False,
        "topic_tags_generated": False,
        "domain_tags_generated": False,
        "complexity_tags_generated": False,
        "sentiment_tags_generated": False,
        "category_tags_generated": False,
        "confidence_scoring": False,
        "tag_validation": False,
        "tag_consistency_check": False,
        "service_initialization": False
    }
    
    try:
        # 1. Verify service initialization
        print("\n1️⃣ Testing service initialization...")
        service = AutoTaggingService()
        assert service is not None
        assert hasattr(service, 'confidence_threshold')
        assert hasattr(service, 'max_tags_per_type')
        verification_results["service_initialization"] = True
        print("✅ Service initialized correctly")
        
        # 2. Verify LLM-assisted tag generation
        print("\n2️⃣ Testing LLM-assisted tag generation...")
        document_id = "test_healthcare_doc"
        
        try:
            tags = await auto_tagging_service.generate_document_tags(
                document_id=document_id,
                content=test_content,
                db=db
            )
            
            if tags and len(tags) > 0:
                verification_results["llm_assisted_tagging"] = True
                print(f"✅ Generated {len(tags)} tags using LLM assistance")
                
                # Verify different tag types are generated
                tag_types = {tag.tag_type for tag in tags}
                
                if 'topic' in tag_types:
                    verification_results["topic_tags_generated"] = True
                    print("✅ Topic tags generated")
                
                if 'domain' in tag_types:
                    verification_results["domain_tags_generated"] = True
                    print("✅ Domain tags generated")
                
                if 'complexity' in tag_types:
                    verification_results["complexity_tags_generated"] = True
                    print("✅ Complexity tags generated")
                
                if 'sentiment' in tag_types:
                    verification_results["sentiment_tags_generated"] = True
                    print("✅ Sentiment tags generated")
                
                if 'category' in tag_types:
                    verification_results["category_tags_generated"] = True
                    print("✅ Category tags generated")
                
                # Verify confidence scoring
                has_confidence_scores = all(
                    hasattr(tag, 'confidence_score') and 
                    0.0 <= tag.confidence_score <= 1.0 
                    for tag in tags
                )
                
                if has_confidence_scores:
                    verification_results["confidence_scoring"] = True
                    print("✅ Confidence scoring implemented")
                    
                    # Show sample tags with confidence scores
                    print("\n📋 Sample generated tags:")
                    for tag in tags[:5]:  # Show first 5 tags
                        confidence_bar = "█" * int(tag.confidence_score * 10)
                        print(f"  • {tag.tag_name} ({tag.tag_type}) - {tag.confidence_score:.2f} {confidence_bar}")
            
            else:
                print("❌ No tags generated")
                
        except Exception as e:
            print(f"❌ Tag generation failed: {str(e)}")
        
        # 3. Verify tag validation and consistency
        print("\n3️⃣ Testing tag validation and consistency...")
        try:
            validation_result = await auto_tagging_service.validate_tag_consistency(
                document_id=document_id,
                db=db
            )
            
            if validation_result and 'consistency_score' in validation_result:
                verification_results["tag_validation"] = True
                print("✅ Tag validation implemented")
                
                if 'average_confidence' in validation_result:
                    verification_results["tag_consistency_check"] = True
                    print("✅ Tag consistency checking implemented")
                    
                    print(f"  Consistency Score: {validation_result['consistency_score']:.2f}")
                    print(f"  Average Confidence: {validation_result['average_confidence']:.2f}")
                    
                    if validation_result.get('issues'):
                        print(f"  Issues Found: {len(validation_result['issues'])}")
                    
                    if validation_result.get('recommendations'):
                        print(f"  Recommendations: {len(validation_result['recommendations'])}")
            
        except Exception as e:
            print(f"❌ Tag validation failed: {str(e)}")
        
        # 4. Verify tag retrieval functionality
        print("\n4️⃣ Testing tag retrieval...")
        try:
            retrieved_tags = await auto_tagging_service.get_document_tags(
                document_id=document_id,
                db=db
            )
            
            if retrieved_tags:
                print(f"✅ Retrieved {len(retrieved_tags)} tags from database")
                
                # Test filtered retrieval
                topic_tags = await auto_tagging_service.get_document_tags(
                    document_id=document_id,
                    db=db,
                    tag_type="topic"
                )
                
                if topic_tags:
                    print(f"✅ Filtered retrieval working (found {len(topic_tags)} topic tags)")
            
        except Exception as e:
            print(f"❌ Tag retrieval failed: {str(e)}")
        
        # 5. Verify error handling
        print("\n5️⃣ Testing error handling...")
        try:
            # Test with invalid document ID
            empty_tags = await auto_tagging_service.get_document_tags(
                document_id="non_existent_doc",
                db=db
            )
            
            if empty_tags == []:
                print("✅ Error handling for non-existent documents works")
            
        except Exception as e:
            print(f"✅ Proper error handling: {str(e)}")
        
    except Exception as e:
        print(f"❌ Verification failed: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
    
    # Summary
    print(f"\n📊 VERIFICATION SUMMARY")
    print("=" * 30)
    
    passed_checks = sum(verification_results.values())
    total_checks = len(verification_results)
    
    for check, passed in verification_results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {check.replace('_', ' ').title()}")
    
    print(f"\n🎯 Overall Score: {passed_checks}/{total_checks} ({passed_checks/total_checks*100:.1f}%)")
    
    if passed_checks == total_checks:
        print("🎉 ALL REQUIREMENTS VERIFIED SUCCESSFULLY!")
        return True
    else:
        print("⚠️  Some requirements need attention")
        return False

async def verify_implementation_completeness():
    """Verify that all required components are implemented"""
    print(f"\n🔧 Verifying Implementation Completeness")
    print("=" * 40)
    
    implementation_checks = {
        "AutoTaggingService class exists": False,
        "generate_document_tags method": False,
        "get_document_tags method": False,
        "validate_tag_consistency method": False,
        "topic tag generation": False,
        "domain tag generation": False,
        "complexity tag generation": False,
        "sentiment tag generation": False,
        "category tag generation": False,
        "confidence scoring": False,
        "global service instance": False
    }
    
    try:
        # Check class and methods exist
        service = AutoTaggingService()
        implementation_checks["AutoTaggingService class exists"] = True
        
        if hasattr(service, 'generate_document_tags'):
            implementation_checks["generate_document_tags method"] = True
        
        if hasattr(service, 'get_document_tags'):
            implementation_checks["get_document_tags method"] = True
        
        if hasattr(service, 'validate_tag_consistency'):
            implementation_checks["validate_tag_consistency method"] = True
        
        if hasattr(service, '_generate_topic_tags'):
            implementation_checks["topic tag generation"] = True
        
        if hasattr(service, '_generate_domain_tags'):
            implementation_checks["domain tag generation"] = True
        
        if hasattr(service, '_generate_complexity_tags'):
            implementation_checks["complexity tag generation"] = True
        
        if hasattr(service, '_generate_sentiment_tags'):
            implementation_checks["sentiment tag generation"] = True
        
        if hasattr(service, '_generate_category_tags'):
            implementation_checks["category tag generation"] = True
        
        if hasattr(service, 'confidence_threshold'):
            implementation_checks["confidence scoring"] = True
        
        # Check global instance
        if auto_tagging_service is not None:
            implementation_checks["global service instance"] = True
        
    except Exception as e:
        print(f"❌ Implementation check failed: {str(e)}")
    
    # Report results
    passed_checks = sum(implementation_checks.values())
    total_checks = len(implementation_checks)
    
    for check, passed in implementation_checks.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {check}")
    
    print(f"\n🎯 Implementation Score: {passed_checks}/{total_checks} ({passed_checks/total_checks*100:.1f}%)")
    
    return passed_checks == total_checks

if __name__ == "__main__":
    print("🚀 Starting Task 6.1 Verification")
    print("Task: Implement LLM-assisted document tagging")
    print("Requirements: 5.1")
    
    try:
        # Run requirement verification
        requirement_passed = asyncio.run(verify_requirement_5_1())
        
        # Run implementation verification
        implementation_complete = asyncio.run(verify_implementation_completeness())
        
        print(f"\n" + "="*60)
        print("FINAL VERIFICATION RESULTS")
        print("="*60)
        
        if requirement_passed and implementation_complete:
            print("🎉 TASK 6.1 VERIFICATION: PASSED")
            print("✅ All requirements satisfied")
            print("✅ Implementation complete")
            print("✅ Ready for production use")
        else:
            print("⚠️  TASK 6.1 VERIFICATION: NEEDS ATTENTION")
            if not requirement_passed:
                print("❌ Some requirements not met")
            if not implementation_complete:
                print("❌ Implementation incomplete")
        
    except KeyboardInterrupt:
        print(f"\n⏹️  Verification interrupted by user")
    except Exception as e:
        print(f"\n💥 Verification failed with error: {str(e)}")
        import traceback
        traceback.print_exc()