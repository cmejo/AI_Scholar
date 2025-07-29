"""
Demo script for testing trend analysis functionality
"""
import asyncio
import json
import sys
import os
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import SessionLocal, Document, DocumentTag, init_db
from services.trend_analyzer import trend_analyzer
from services.auto_tagging_service import auto_tagging_service

async def create_sample_data():
    """Create sample documents and tags for testing"""
    db = SessionLocal()
    
    try:
        # Create sample user
        user_id = "test_user_trend_analysis"
        
        # Create sample documents with different timestamps
        base_time = datetime.now() - timedelta(days=20)
        
        documents_data = [
            {
                "id": "trend_doc_1",
                "name": "Introduction to Machine Learning",
                "content": "Machine learning is a subset of artificial intelligence that focuses on algorithms and statistical models. This comprehensive guide covers supervised learning, unsupervised learning, and reinforcement learning techniques.",
                "size": 45000,
                "created_at": base_time
            },
            {
                "id": "trend_doc_2", 
                "name": "Deep Learning Fundamentals",
                "content": "Deep learning uses neural networks with multiple layers to model and understand complex patterns. This tutorial covers convolutional neural networks, recurrent neural networks, and transformer architectures.",
                "size": 62000,
                "created_at": base_time + timedelta(days=3)
            },
            {
                "id": "trend_doc_3",
                "name": "Natural Language Processing Guide",
                "content": "Natural language processing combines computational linguistics with machine learning to help computers understand human language. Topics include tokenization, sentiment analysis, and language models.",
                "size": 38000,
                "created_at": base_time + timedelta(days=7)
            },
            {
                "id": "trend_doc_4",
                "name": "Computer Vision Applications",
                "content": "Computer vision enables machines to interpret and understand visual information. This guide covers image classification, object detection, and image segmentation using deep learning.",
                "size": 55000,
                "created_at": base_time + timedelta(days=10)
            },
            {
                "id": "trend_doc_5",
                "name": "AI Ethics and Bias",
                "content": "As artificial intelligence becomes more prevalent, understanding ethics and bias in AI systems is crucial. This paper discusses fairness, accountability, and transparency in machine learning.",
                "size": 41000,
                "created_at": base_time + timedelta(days=14)
            },
            {
                "id": "trend_doc_6",
                "name": "Reinforcement Learning Tutorial",
                "content": "Reinforcement learning is a type of machine learning where agents learn to make decisions through interaction with an environment. This tutorial covers Q-learning, policy gradients, and actor-critic methods.",
                "size": 48000,
                "created_at": base_time + timedelta(days=16)
            }
        ]
        
        # Create documents in database
        for doc_data in documents_data:
            # Check if document already exists
            existing_doc = db.query(Document).filter(Document.id == doc_data["id"]).first()
            if not existing_doc:
                document = Document(
                    id=doc_data["id"],
                    user_id=user_id,
                    name=doc_data["name"],
                    file_path=f"/tmp/{doc_data['name']}.pdf",
                    content_type="application/pdf",
                    size=doc_data["size"],
                    status="completed",
                    chunks_count=10,
                    embeddings_count=10,
                    created_at=doc_data["created_at"]
                )
                db.add(document)
        
        db.commit()
        
        # Generate tags for each document
        for doc_data in documents_data:
            print(f"Generating tags for: {doc_data['name']}")
            
            # Check if tags already exist
            existing_tags = db.query(DocumentTag).filter(
                DocumentTag.document_id == doc_data["id"]
            ).first()
            
            if not existing_tags:
                try:
                    tags = await auto_tagging_service.generate_document_tags(
                        document_id=doc_data["id"],
                        content=doc_data["content"],
                        db=db
                    )
                    print(f"Generated {len(tags)} tags for {doc_data['name']}")
                except Exception as e:
                    print(f"Error generating tags for {doc_data['name']}: {str(e)}")
                    # Create some manual tags as fallback
                    manual_tags = create_manual_tags(doc_data["id"], doc_data["name"])
                    for tag_data in manual_tags:
                        tag = DocumentTag(**tag_data)
                        db.add(tag)
                    db.commit()
        
        print("Sample data created successfully!")
        return user_id
        
    except Exception as e:
        print(f"Error creating sample data: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

def create_manual_tags(document_id: str, document_name: str):
    """Create manual tags based on document name"""
    tags = []
    
    # Topic tags based on document name
    if "machine learning" in document_name.lower():
        tags.extend([
            {
                "document_id": document_id,
                "tag_name": "machine_learning",
                "tag_type": "topic",
                "confidence_score": 0.9,
                "generated_by": "manual"
            },
            {
                "document_id": document_id,
                "tag_name": "artificial_intelligence",
                "tag_type": "topic",
                "confidence_score": 0.85,
                "generated_by": "manual"
            }
        ])
    
    if "deep learning" in document_name.lower():
        tags.extend([
            {
                "document_id": document_id,
                "tag_name": "deep_learning",
                "tag_type": "topic",
                "confidence_score": 0.95,
                "generated_by": "manual"
            },
            {
                "document_id": document_id,
                "tag_name": "neural_networks",
                "tag_type": "topic",
                "confidence_score": 0.9,
                "generated_by": "manual"
            }
        ])
    
    if "nlp" in document_name.lower() or "natural language" in document_name.lower():
        tags.extend([
            {
                "document_id": document_id,
                "tag_name": "natural_language_processing",
                "tag_type": "topic",
                "confidence_score": 0.9,
                "generated_by": "manual"
            },
            {
                "document_id": document_id,
                "tag_name": "computational_linguistics",
                "tag_type": "topic",
                "confidence_score": 0.8,
                "generated_by": "manual"
            }
        ])
    
    if "computer vision" in document_name.lower():
        tags.extend([
            {
                "document_id": document_id,
                "tag_name": "computer_vision",
                "tag_type": "topic",
                "confidence_score": 0.9,
                "generated_by": "manual"
            },
            {
                "document_id": document_id,
                "tag_name": "image_processing",
                "tag_type": "topic",
                "confidence_score": 0.85,
                "generated_by": "manual"
            }
        ])
    
    if "ethics" in document_name.lower():
        tags.extend([
            {
                "document_id": document_id,
                "tag_name": "ai_ethics",
                "tag_type": "topic",
                "confidence_score": 0.9,
                "generated_by": "manual"
            },
            {
                "document_id": document_id,
                "tag_name": "bias_fairness",
                "tag_type": "topic",
                "confidence_score": 0.85,
                "generated_by": "manual"
            }
        ])
    
    if "reinforcement" in document_name.lower():
        tags.extend([
            {
                "document_id": document_id,
                "tag_name": "reinforcement_learning",
                "tag_type": "topic",
                "confidence_score": 0.9,
                "generated_by": "manual"
            },
            {
                "document_id": document_id,
                "tag_name": "decision_making",
                "tag_type": "topic",
                "confidence_score": 0.8,
                "generated_by": "manual"
            }
        ])
    
    # Domain tags
    tags.append({
        "document_id": document_id,
        "tag_name": "computer_science",
        "tag_type": "domain",
        "confidence_score": 0.95,
        "generated_by": "manual"
    })
    
    tags.append({
        "document_id": document_id,
        "tag_name": "artificial_intelligence",
        "tag_type": "domain",
        "confidence_score": 0.9,
        "generated_by": "manual"
    })
    
    # Complexity tags
    if "introduction" in document_name.lower() or "fundamentals" in document_name.lower():
        complexity = "complexity_intermediate"
    elif "tutorial" in document_name.lower() or "guide" in document_name.lower():
        complexity = "complexity_beginner"
    else:
        complexity = "complexity_advanced"
    
    tags.append({
        "document_id": document_id,
        "tag_name": complexity,
        "tag_type": "complexity",
        "confidence_score": 0.8,
        "generated_by": "manual"
    })
    
    return tags

async def test_trend_analysis():
    """Test trend analysis functionality"""
    print("=== Testing Trend Analysis ===")
    
    db = SessionLocal()
    
    try:
        # Create sample data
        user_id = await create_sample_data()
        
        print("\n1. Testing Document Collection Trend Analysis...")
        
        # Test trend analysis
        trend_results = await trend_analyzer.analyze_document_collection_trends(
            user_id=user_id,
            db=db,
            time_range_days=30
        )
        
        print(f"Trend Analysis Status: {trend_results['status']}")
        print(f"Documents Analyzed: {trend_results['document_count']}")
        
        if trend_results['status'] == 'success':
            trends = trend_results['trends']
            
            # Display tag trends
            if 'tag_trends' in trends:
                print("\n--- Tag Trends ---")
                for tag_type, data in trends['tag_trends'].items():
                    print(f"{tag_type.upper()}:")
                    print(f"  Total tags: {data['total_tags']}")
                    print(f"  Unique tags: {data['unique_tags']}")
                    print(f"  Average confidence: {data['average_confidence']:.2f}")
                    
                    if data['trending_tags']:
                        print("  Trending tags:")
                        for tag in data['trending_tags'][:3]:
                            print(f"    - {tag['tag_name']}: {tag['frequency']} occurrences, {tag['average_confidence']:.2f} confidence")
            
            # Display temporal trends
            if 'temporal_trends' in trends:
                print("\n--- Temporal Trends ---")
                temporal = trends['temporal_trends']
                stats = temporal.get('statistics', {})
                print(f"Average daily uploads: {stats.get('average_daily_uploads', 0):.2f}")
                print(f"Total active days: {stats.get('total_days_active', 0)}")
                
                if temporal.get('patterns'):
                    print("Patterns detected:")
                    for pattern in temporal['patterns']:
                        print(f"  - {pattern['description']} (confidence: {pattern['confidence']:.2f})")
            
            # Display topic evolution
            if 'topic_evolution' in trends and trends['topic_evolution'].get('status') != 'no_topic_data':
                print("\n--- Topic Evolution ---")
                topic_evo = trends['topic_evolution']
                print(f"Total topics tracked: {topic_evo.get('total_topics_tracked', 0)}")
                
                if topic_evo.get('emerging_topics'):
                    print(f"Emerging topics: {', '.join(topic_evo['emerging_topics'])}")
                
                if topic_evo.get('declining_topics'):
                    print(f"Declining topics: {', '.join(topic_evo['declining_topics'])}")
            
            # Display insights
            if trend_results.get('insights'):
                print("\n--- Generated Insights ---")
                for insight in trend_results['insights']:
                    print(f"- {insight['insight']} (confidence: {insight['confidence']:.2f})")
                    print(f"  Recommendation: {insight['recommendation']}")
        
        print("\n2. Testing Document Comparison...")
        
        # Test document comparison
        document_ids = ["trend_doc_1", "trend_doc_2", "trend_doc_3"]
        
        comparison_results = await trend_analyzer.compare_documents(
            document_ids=document_ids,
            db=db
        )
        
        print(f"Comparing {len(comparison_results['documents'])} documents:")
        for doc in comparison_results['documents']:
            print(f"  - {doc['name']} (ID: {doc['id']})")
        
        # Display comparison results
        comparisons = comparison_results['comparisons']
        
        if 'tag_comparison' in comparisons:
            print("\n--- Tag Comparison ---")
            for pair_key, tag_data in comparisons['tag_comparison'].items():
                print(f"{pair_key}:")
                for tag_type, type_data in tag_data.items():
                    overlap = type_data['overlap_score']
                    print(f"  {tag_type}: {overlap:.2f} overlap")
                    if type_data['common_tags']:
                        print(f"    Common: {', '.join(type_data['common_tags'])}")
        
        # Display overall similarity
        if comparison_results.get('overall_similarity'):
            print("\n--- Overall Similarity Scores ---")
            for pair, similarity in comparison_results['overall_similarity'].items():
                print(f"{pair}: {similarity:.2f}")
        
        # Display comparison insights
        if comparison_results.get('insights'):
            print("\n--- Comparison Insights ---")
            for insight in comparison_results['insights']:
                print(f"- {insight['insight']}")
                if 'common_elements' in insight:
                    print(f"  Common elements: {', '.join(insight['common_elements'])}")
        
        print("\n3. Testing Specific Comparison Aspects...")
        
        # Test specific comparison aspects
        specific_comparison = await trend_analyzer.compare_documents(
            document_ids=["trend_doc_1", "trend_doc_4"],
            db=db,
            comparison_aspects=["topics", "complexity", "domains"]
        )
        
        print("Specific aspect comparison completed:")
        print(f"Aspects analyzed: {list(specific_comparison['comparisons'].keys())}")
        
        print("\n=== Trend Analysis Testing Complete ===")
        
    except Exception as e:
        print(f"Error during trend analysis testing: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

async def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n=== Testing Edge Cases ===")
    
    db = SessionLocal()
    
    try:
        # Test with insufficient documents
        print("1. Testing with insufficient documents...")
        
        result = await trend_analyzer.analyze_document_collection_trends(
            user_id="nonexistent_user",
            db=db,
            time_range_days=30
        )
        
        print(f"Result with no documents: {result['status']}")
        
        # Test comparison with invalid document IDs
        print("\n2. Testing comparison with invalid document IDs...")
        
        try:
            await trend_analyzer.compare_documents(
                document_ids=["invalid_doc_1", "invalid_doc_2"],
                db=db
            )
        except ValueError as e:
            print(f"Expected error caught: {str(e)}")
        
        # Test comparison with insufficient documents
        print("\n3. Testing comparison with insufficient documents...")
        
        try:
            await trend_analyzer.compare_documents(
                document_ids=["single_doc"],
                db=db
            )
        except ValueError as e:
            print(f"Expected error caught: {str(e)}")
        
        print("\n=== Edge Case Testing Complete ===")
        
    except Exception as e:
        print(f"Error during edge case testing: {str(e)}")
    finally:
        db.close()

async def main():
    """Main function to run all tests"""
    print("Starting Trend Analysis Demo...")
    
    # Initialize database
    await init_db()
    
    # Run tests
    await test_trend_analysis()
    await test_edge_cases()
    
    print("\nDemo completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())