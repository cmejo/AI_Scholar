#!/usr/bin/env python3
"""
Demo script for AutoTaggingService functionality
"""
import asyncio
import json
from datetime import datetime
from sqlalchemy.orm import Session

from core.database import get_db, init_db, Document, DocumentTag
from services.auto_tagging_service import auto_tagging_service
from models.schemas import TagType

async def demo_auto_tagging():
    """Demonstrate auto-tagging functionality"""
    print("🏷️  Auto-Tagging Service Demo")
    print("=" * 50)
    
    # Initialize database
    await init_db()
    
    # Sample document content for testing
    sample_documents = [
        {
            "id": "doc_ml_guide",
            "content": """
            Machine Learning: A Comprehensive Guide
            
            This document provides an in-depth exploration of machine learning algorithms
            and their practical applications in modern data science. We cover supervised
            learning techniques including linear regression, decision trees, and neural
            networks. The guide also explores unsupervised learning methods such as
            clustering and dimensionality reduction.
            
            Key topics include:
            - Feature engineering and selection
            - Model evaluation and validation
            - Overfitting and regularization techniques
            - Deep learning fundamentals
            - Real-world case studies in computer vision and natural language processing
            
            This material is designed for intermediate to advanced practitioners who want
            to deepen their understanding of algorithmic approaches to artificial intelligence.
            The examples use Python with popular libraries like scikit-learn, TensorFlow,
            and PyTorch.
            """
        },
        {
            "id": "doc_legal_contract",
            "content": """
            Software License Agreement
            
            This Software License Agreement ("Agreement") is entered into between
            the Licensor and the Licensee for the use of proprietary software.
            
            TERMS AND CONDITIONS:
            
            1. Grant of License: Subject to the terms of this Agreement, Licensor
            hereby grants to Licensee a non-exclusive, non-transferable license
            to use the Software.
            
            2. Restrictions: Licensee shall not modify, reverse engineer, or
            distribute the Software without prior written consent.
            
            3. Termination: This Agreement may be terminated by either party
            with thirty (30) days written notice.
            
            4. Limitation of Liability: In no event shall Licensor be liable
            for any indirect, incidental, or consequential damages.
            
            This agreement is governed by the laws of the State of California.
            """
        },
        {
            "id": "doc_cooking_recipe",
            "content": """
            Classic Italian Carbonara Recipe
            
            Ingredients:
            - 400g spaghetti
            - 200g guanciale or pancetta, diced
            - 4 large eggs
            - 100g Pecorino Romano cheese, grated
            - Black pepper, freshly ground
            - Salt for pasta water
            
            Instructions:
            1. Bring a large pot of salted water to boil. Cook spaghetti until al dente.
            2. While pasta cooks, render the guanciale in a large pan until crispy.
            3. In a bowl, whisk together eggs, cheese, and plenty of black pepper.
            4. Reserve 1 cup pasta water before draining.
            5. Add hot pasta to the pan with guanciale.
            6. Remove from heat and quickly stir in egg mixture, adding pasta water as needed.
            7. Serve immediately with extra cheese and pepper.
            
            Tips: The key is to work quickly and keep the pan off heat when adding eggs
            to prevent scrambling. This traditional Roman dish should be creamy, not dry.
            """
        }
    ]
    
    # Get database session
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        for doc_data in sample_documents:
            print(f"\n📄 Processing Document: {doc_data['id']}")
            print("-" * 40)
            
            # Generate tags for the document
            print("🔄 Generating tags...")
            try:
                tags = await auto_tagging_service.generate_document_tags(
                    document_id=doc_data['id'],
                    content=doc_data['content'],
                    db=db
                )
                
                print(f"✅ Generated {len(tags)} tags:")
                
                # Group tags by type
                tags_by_type = {}
                for tag in tags:
                    if tag.tag_type not in tags_by_type:
                        tags_by_type[tag.tag_type] = []
                    tags_by_type[tag.tag_type].append(tag)
                
                # Display tags by type
                for tag_type, type_tags in tags_by_type.items():
                    print(f"\n  📋 {tag_type.upper()} Tags:")
                    for tag in type_tags:
                        confidence_bar = "█" * int(tag.confidence_score * 10)
                        print(f"    • {tag.tag_name} (confidence: {tag.confidence_score:.2f}) {confidence_bar}")
                
                # Validate tag consistency
                print("\n🔍 Validating tag consistency...")
                validation_result = await auto_tagging_service.validate_tag_consistency(
                    document_id=doc_data['id'],
                    db=db
                )
                
                print(f"  Consistency Score: {validation_result['consistency_score']:.2f}")
                print(f"  Average Confidence: {validation_result['average_confidence']:.2f}")
                
                if validation_result['issues']:
                    print("  ⚠️  Issues found:")
                    for issue in validation_result['issues']:
                        print(f"    - {issue}")
                
                if validation_result['recommendations']:
                    print("  💡 Recommendations:")
                    for rec in validation_result['recommendations']:
                        print(f"    - {rec}")
                
                print(f"  📊 Tag Distribution: {validation_result['tag_distribution']}")
                
            except Exception as e:
                print(f"❌ Error generating tags: {str(e)}")
                continue
        
        # Demonstrate tag retrieval
        print(f"\n🔍 Retrieving tags for first document...")
        retrieved_tags = await auto_tagging_service.get_document_tags(
            document_id=sample_documents[0]['id'],
            db=db
        )
        
        print(f"📋 Retrieved {len(retrieved_tags)} tags:")
        for tag in retrieved_tags[:5]:  # Show first 5 tags
            print(f"  • {tag.tag_name} ({tag.tag_type}) - {tag.confidence_score:.2f}")
        
        # Demonstrate filtered tag retrieval
        print(f"\n🎯 Retrieving only 'topic' tags...")
        topic_tags = await auto_tagging_service.get_document_tags(
            document_id=sample_documents[0]['id'],
            db=db,
            tag_type="topic"
        )
        
        print(f"📋 Retrieved {len(topic_tags)} topic tags:")
        for tag in topic_tags:
            print(f"  • {tag.tag_name} - {tag.confidence_score:.2f}")
        
        print(f"\n✅ Auto-tagging demo completed successfully!")
        
    except Exception as e:
        print(f"❌ Demo failed: {str(e)}")
        raise
    finally:
        db.close()

async def demo_tag_accuracy():
    """Demonstrate tag accuracy and consistency testing"""
    print(f"\n🎯 Tag Accuracy Testing")
    print("=" * 30)
    
    # Test with known content types
    test_cases = [
        {
            "content": "This research paper investigates the effectiveness of transformer architectures in natural language processing tasks.",
            "expected_tags": ["research_paper", "natural_language_processing", "computer_science", "complexity_advanced"]
        },
        {
            "content": "Step-by-step tutorial for beginners on how to create your first website using HTML and CSS.",
            "expected_tags": ["tutorial", "web_development", "beginner", "technology"]
        },
        {
            "content": "Quarterly financial report showing revenue growth and market analysis for the technology sector.",
            "expected_tags": ["report", "business", "finance", "formal"]
        }
    ]
    
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        accuracy_scores = []
        
        for i, test_case in enumerate(test_cases):
            print(f"\n📝 Test Case {i+1}:")
            print(f"Content preview: {test_case['content'][:100]}...")
            
            # Generate tags
            tags = await auto_tagging_service.generate_document_tags(
                document_id=f"test_doc_{i}",
                content=test_case['content'],
                db=db
            )
            
            generated_tag_names = [tag.tag_name for tag in tags]
            expected_tags = test_case['expected_tags']
            
            # Calculate accuracy (simple overlap measure)
            matches = sum(1 for expected in expected_tags 
                         if any(expected.lower() in generated.lower() or generated.lower() in expected.lower() 
                               for generated in generated_tag_names))
            
            accuracy = matches / len(expected_tags) if expected_tags else 0
            accuracy_scores.append(accuracy)
            
            print(f"  Generated tags: {generated_tag_names[:5]}")  # Show first 5
            print(f"  Expected tags: {expected_tags}")
            print(f"  Accuracy: {accuracy:.2f} ({matches}/{len(expected_tags)} matches)")
        
        overall_accuracy = sum(accuracy_scores) / len(accuracy_scores)
        print(f"\n📊 Overall Accuracy: {overall_accuracy:.2f}")
        
    except Exception as e:
        print(f"❌ Accuracy testing failed: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Starting Auto-Tagging Service Demo")
    
    try:
        # Run main demo
        asyncio.run(demo_auto_tagging())
        
        # Run accuracy testing
        asyncio.run(demo_tag_accuracy())
        
        print(f"\n🎉 All demos completed successfully!")
        
    except KeyboardInterrupt:
        print(f"\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n💥 Demo failed with error: {str(e)}")
        import traceback
        traceback.print_exc()