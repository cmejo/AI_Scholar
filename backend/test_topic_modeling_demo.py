"""
Demo script for Topic Modeling Service
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from core.database import SessionLocal, Document, DocumentChunk, User, init_db
from services.topic_modeling_service import TopicModelingService
import uuid

async def create_sample_data(db: Session):
    """Create sample documents and chunks for testing"""
    print("Creating sample data...")
    
    # Try to get existing user or create a new one
    user = db.query(User).filter(User.email == "test@example.com").first()
    if not user:
        user = User(
            id=str(uuid.uuid4()),
            email="test@example.com",
            name="Test User",
            hashed_password="hashed_password"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        print("Using existing test user")
    
    # Sample document contents
    sample_docs = [
        {
            "name": "Machine Learning Fundamentals",
            "chunks": [
                "Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed. It focuses on developing algorithms that can access data and use it to learn for themselves.",
                "Supervised learning algorithms build a mathematical model of training data that contains both inputs and desired outputs. Common supervised learning algorithms include linear regression, logistic regression, and support vector machines.",
                "Deep learning is a subset of machine learning that uses artificial neural networks with multiple layers. These networks can learn complex patterns in data and have achieved remarkable success in image recognition, natural language processing, and speech recognition."
            ]
        },
        {
            "name": "Data Science Handbook",
            "chunks": [
                "Data science is an interdisciplinary field that combines statistics, mathematics, programming, and domain expertise to extract meaningful insights from data. It involves collecting, cleaning, analyzing, and interpreting large datasets.",
                "Statistical analysis is fundamental to data science. It includes descriptive statistics, inferential statistics, hypothesis testing, and regression analysis. These techniques help identify patterns, relationships, and trends in data.",
                "Data visualization is crucial for communicating findings effectively. Tools like matplotlib, seaborn, and plotly help create charts, graphs, and interactive visualizations that make complex data understandable to stakeholders."
            ]
        },
        {
            "name": "Artificial Intelligence Overview",
            "chunks": [
                "Artificial intelligence refers to the simulation of human intelligence in machines that are programmed to think and learn like humans. AI systems can perform tasks that typically require human intelligence, such as visual perception, speech recognition, and decision-making.",
                "Natural language processing is a branch of AI that helps computers understand, interpret, and manipulate human language. NLP combines computational linguistics with statistical and machine learning models to enable computers to process human language in a valuable way.",
                "Computer vision is another important AI field that enables machines to interpret and understand visual information from the world. It involves developing algorithms that can identify objects, faces, scenes, and activities in images and videos."
            ]
        },
        {
            "name": "Python Programming Guide",
            "chunks": [
                "Python is a high-level, interpreted programming language known for its simplicity and readability. It supports multiple programming paradigms including procedural, object-oriented, and functional programming.",
                "Python's extensive standard library and third-party packages make it ideal for various applications including web development, data analysis, machine learning, and scientific computing. Popular libraries include NumPy, Pandas, Scikit-learn, and TensorFlow.",
                "Object-oriented programming in Python allows developers to create reusable code through classes and objects. Key concepts include inheritance, encapsulation, and polymorphism, which help organize code and make it more maintainable."
            ]
        },
        {
            "name": "Database Systems",
            "chunks": [
                "Database systems are organized collections of data that are stored and accessed electronically. They provide efficient ways to store, retrieve, and manage large amounts of information while ensuring data integrity and security.",
                "Relational databases use structured query language (SQL) to manage data stored in tables with rows and columns. Popular relational database management systems include MySQL, PostgreSQL, and SQLite.",
                "NoSQL databases are designed to handle unstructured or semi-structured data and can scale horizontally across multiple servers. Types include document databases, key-value stores, column-family databases, and graph databases."
            ]
        }
    ]
    
    # Create documents and chunks
    documents = []
    for i, doc_data in enumerate(sample_docs):
        doc = Document(
            id=str(uuid.uuid4()),
            user_id=user.id,
            name=doc_data["name"],
            file_path=f"/fake/path/{doc_data['name'].lower().replace(' ', '_')}.pdf",
            content_type="application/pdf",
            size=len(" ".join(doc_data["chunks"])),
            status="completed",
            chunks_count=len(doc_data["chunks"]),
            embeddings_count=len(doc_data["chunks"]),
            created_at=datetime.utcnow() - timedelta(days=10-i*2)
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        documents.append(doc)
        
        # Create chunks for this document
        for j, chunk_content in enumerate(doc_data["chunks"]):
            chunk = DocumentChunk(
                id=str(uuid.uuid4()),
                document_id=doc.id,
                content=chunk_content,
                chunk_index=j,
                page_number=j + 1,
                chunk_metadata="{}"
            )
            db.add(chunk)
        
        db.commit()
    
    print(f"Created {len(documents)} documents with chunks")
    return user, documents

async def test_topic_modeling():
    """Test the topic modeling service"""
    print("=== Topic Modeling Service Demo ===\n")
    
    # Initialize database
    await init_db()
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Create sample data
        user, documents = await create_sample_data(db)
        
        # Initialize topic modeling service
        topic_service = TopicModelingService(db)
        
        print("1. Performing comprehensive topic analysis...")
        result = await topic_service.analyze_document_topics(
            user_id=user.id,
            n_topics=5,
            update_tags=True
        )
        
        print(f"\nAnalysis Results:")
        print(f"- Found {len(result.topics)} topics")
        print(f"- Created {len(result.document_clusters)} document clusters")
        print(f"- Analyzed {len(result.topic_trends)} topic trends")
        print(f"- Processed {result.model_metadata.get('n_documents', 0)} documents")
        
        print("\n2. Topic Details:")
        for i, topic in enumerate(result.topics):
            print(f"\nTopic {i+1}: {topic.name}")
            print(f"  Keywords: {', '.join(topic.keywords[:5])}")
            print(f"  Document Count: {topic.document_count}")
            print(f"  Weight: {topic.weight:.3f}")
            print(f"  Description: {topic.description}")
        
        print("\n3. Document Clusters:")
        for cluster in result.document_clusters:
            print(f"\nCluster {cluster.id+1}: {cluster.name}")
            print(f"  Size: {cluster.cluster_size} documents")
            print(f"  Keywords: {', '.join(cluster.centroid_keywords[:5])}")
            print(f"  Similarity: {cluster.similarity_threshold:.3f}")
        
        print("\n4. Topic Trends:")
        for trend in result.topic_trends:
            print(f"\nTopic: {trend.topic_name}")
            print(f"  Trend: {trend.trend_direction}")
            print(f"  Growth Rate: {trend.growth_rate:.3f}")
            print(f"  Current Strength: {trend.current_strength:.3f}")
        
        print("\n5. Document-Topic Assignments:")
        for doc_id, assignments in result.document_topic_assignments.items():
            doc = db.query(Document).filter(Document.id == doc_id).first()
            if doc and assignments:
                print(f"\n{doc.name}:")
                for topic_id, weight in assignments[:3]:  # Top 3 topics
                    topic_name = result.topics[topic_id].name if topic_id < len(result.topics) else f"Topic {topic_id}"
                    print(f"  - {topic_name}: {weight:.3f}")
        
        print("\n6. Testing document similarity...")
        if documents:
            similarities = await topic_service.get_document_similarities(
                document_id=documents[0].id,
                top_k=3,
                similarity_threshold=0.1
            )
            
            print(f"\nDocuments similar to '{documents[0].name}':")
            for sim in similarities:
                print(f"  - {sim['document_name']}: {sim['similarity_score']:.3f}")
        
        print("\n7. Getting comprehensive topic insights...")
        insights = await topic_service.get_topic_insights(user_id=user.id)
        
        print(f"\nTopic Insights Summary:")
        print(f"  - Total Topics: {insights['topic_summary']['total_topics']}")
        print(f"  - Total Clusters: {insights['topic_summary']['total_clusters']}")
        print(f"  - Most Prominent Topic: {insights['topic_summary']['most_prominent_topic']}")
        print(f"  - Largest Cluster Size: {insights['topic_summary']['largest_cluster_size']}")
        
        print(f"\nTrending Topics:")
        for trend in insights['trending_topics']:
            print(f"  - {trend['topic_name']}: {trend['trend_direction']} ({trend['growth_rate']:.3f})")
        
        print("\n8. Verifying document tags were updated...")
        from core.database import DocumentTag
        tags = db.query(DocumentTag).filter(
            DocumentTag.tag_type == "topic",
            DocumentTag.generated_by == "topic_modeling"
        ).all()
        
        print(f"\nGenerated {len(tags)} topic tags:")
        for tag in tags[:10]:  # Show first 10 tags
            doc = db.query(Document).filter(Document.id == tag.document_id).first()
            print(f"  - {doc.name if doc else 'Unknown'}: {tag.tag_name} ({tag.confidence_score:.3f})")
        
        print("\n=== Topic Modeling Demo Completed Successfully! ===")
        
    except Exception as e:
        print(f"Error during demo: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_topic_modeling())