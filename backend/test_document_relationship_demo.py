"""
Demo script for Document Relationship Mapping functionality
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import List, Dict, Any

from core.database import (
    get_db, Document, DocumentChunk, KnowledgeGraphEntity, 
    KnowledgeGraphRelationship, DocumentTag, User
)
from services.document_relationship_mapper import DocumentRelationshipMapper
from models.schemas import DocumentResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentRelationshipDemo:
    """Demo class for document relationship mapping"""
    
    def __init__(self):
        self.db = next(get_db())
        self.mapper = DocumentRelationshipMapper(self.db)
        self.demo_user_id = "demo_user_relationship"
    
    async def setup_demo_data(self):
        """Set up demo documents with relationships"""
        logger.info("Setting up demo data for document relationship mapping...")
        
        # Create demo user if not exists
        existing_user = self.db.query(User).filter(User.id == self.demo_user_id).first()
        if not existing_user:
            demo_user = User(
                id=self.demo_user_id,
                email="demo@relationship.com",
                name="Relationship Demo User",
                hashed_password="demo_hash"
            )
            self.db.add(demo_user)
        
        # Sample documents with related content
        demo_documents = [
            {
                "id": "doc_ai_intro",
                "name": "Introduction to Artificial Intelligence",
                "content": """
                Artificial Intelligence (AI) is a branch of computer science that aims to create 
                intelligent machines that can perform tasks that typically require human intelligence. 
                Machine learning is a subset of AI that enables computers to learn and improve from 
                experience without being explicitly programmed. Deep learning, a subset of machine 
                learning, uses neural networks with multiple layers to model and understand complex 
                patterns in data.
                """,
                "tags": ["AI", "machine learning", "technology", "computer science"],
                "entities": ["Artificial Intelligence", "Machine Learning", "Deep Learning", "Neural Networks"]
            },
            {
                "id": "doc_ml_algorithms",
                "name": "Machine Learning Algorithms Overview",
                "content": """
                Machine learning algorithms can be categorized into supervised learning, unsupervised 
                learning, and reinforcement learning. Supervised learning uses labeled data to train 
                models, including algorithms like linear regression, decision trees, and support vector 
                machines. Unsupervised learning finds patterns in unlabeled data using techniques like 
                clustering and dimensionality reduction. Neural networks form the foundation of deep 
                learning approaches.
                """,
                "tags": ["machine learning", "algorithms", "supervised learning", "neural networks"],
                "entities": ["Machine Learning", "Supervised Learning", "Unsupervised Learning", "Neural Networks", "Decision Trees"]
            },
            {
                "id": "doc_nlp_guide",
                "name": "Natural Language Processing Guide",
                "content": """
                Natural Language Processing (NLP) is a field of artificial intelligence that focuses 
                on the interaction between computers and human language. NLP combines computational 
                linguistics with machine learning and deep learning to help computers understand, 
                interpret, and generate human language. Common NLP tasks include sentiment analysis, 
                named entity recognition, machine translation, and text summarization.
                """,
                "tags": ["NLP", "AI", "machine learning", "linguistics"],
                "entities": ["Natural Language Processing", "Artificial Intelligence", "Machine Learning", "Computational Linguistics"]
            },
            {
                "id": "doc_data_science",
                "name": "Data Science Fundamentals",
                "content": """
                Data science is an interdisciplinary field that uses scientific methods, processes, 
                algorithms, and systems to extract knowledge and insights from structured and 
                unstructured data. It combines statistics, mathematics, programming, and domain 
                expertise. Machine learning is a key component of data science, along with data 
                visualization, statistical analysis, and big data technologies.
                """,
                "tags": ["data science", "statistics", "machine learning", "analytics"],
                "entities": ["Data Science", "Machine Learning", "Statistics", "Big Data"]
            },
            {
                "id": "doc_python_programming",
                "name": "Python Programming for Beginners",
                "content": """
                Python is a high-level, interpreted programming language known for its simplicity 
                and readability. It's widely used in web development, data analysis, artificial 
                intelligence, and scientific computing. Python's extensive library ecosystem makes 
                it particularly popular for machine learning projects, with libraries like scikit-learn, 
                TensorFlow, and PyTorch providing powerful tools for AI development.
                """,
                "tags": ["Python", "programming", "data analysis", "AI"],
                "entities": ["Python", "Programming", "Artificial Intelligence", "TensorFlow", "PyTorch"]
            }
        ]
        
        # Create documents and related data
        for doc_data in demo_documents:
            # Check if document already exists
            existing_doc = self.db.query(Document).filter(Document.id == doc_data["id"]).first()
            if existing_doc:
                continue
            
            # Create document
            document = Document(
                id=doc_data["id"],
                name=doc_data["name"],
                user_id=self.demo_user_id,
                file_path=f"/demo/{doc_data['id']}.txt",
                size=len(doc_data["content"]),
                status="processed",
                chunks_count=1,
                embeddings_count=1,
                content_type="text/plain"
            )
            self.db.add(document)
            
            # Create document chunk
            chunk = DocumentChunk(
                id=f"{doc_data['id']}_chunk_1",
                document_id=doc_data["id"],
                content=doc_data["content"].strip(),
                chunk_index=0,
                page_number=1
            )
            self.db.add(chunk)
            
            # Create document tags
            for tag_name in doc_data["tags"]:
                tag = DocumentTag(
                    document_id=doc_data["id"],
                    tag_name=tag_name,
                    tag_type="topic",
                    confidence_score=0.9,
                    generated_by="demo"
                )
                self.db.add(tag)
            
            # Create knowledge graph entities
            for entity_name in doc_data["entities"]:
                entity = KnowledgeGraphEntity(
                    name=entity_name,
                    type="CONCEPT",
                    document_id=doc_data["id"],
                    importance_score=0.8,
                    metadata={"source": "demo"}
                )
                self.db.add(entity)
        
        # Create some relationships between entities
        relationships = [
            ("Artificial Intelligence", "Machine Learning", "CONTAINS"),
            ("Machine Learning", "Deep Learning", "CONTAINS"),
            ("Machine Learning", "Neural Networks", "USES"),
            ("Natural Language Processing", "Artificial Intelligence", "PART_OF"),
            ("Data Science", "Machine Learning", "USES"),
            ("Python", "Machine Learning", "USED_FOR")
        ]
        
        for source_name, target_name, rel_type in relationships:
            source_entity = self.db.query(KnowledgeGraphEntity).filter(
                KnowledgeGraphEntity.name == source_name
            ).first()
            target_entity = self.db.query(KnowledgeGraphEntity).filter(
                KnowledgeGraphEntity.name == target_name
            ).first()
            
            if source_entity and target_entity:
                # Check if relationship already exists
                existing_rel = self.db.query(KnowledgeGraphRelationship).filter(
                    KnowledgeGraphRelationship.source_entity_id == source_entity.id,
                    KnowledgeGraphRelationship.target_entity_id == target_entity.id
                ).first()
                
                if not existing_rel:
                    relationship = KnowledgeGraphRelationship(
                        source_entity_id=source_entity.id,
                        target_entity_id=target_entity.id,
                        relationship_type=rel_type,
                        confidence_score=0.9,
                        context="Demo relationship",
                        metadata={"source": "demo"}
                    )
                    self.db.add(relationship)
        
        self.db.commit()
        logger.info("Demo data setup completed!")
    
    async def demonstrate_relationship_analysis(self):
        """Demonstrate document relationship analysis"""
        logger.info("\n" + "="*60)
        logger.info("DOCUMENT RELATIONSHIP ANALYSIS DEMO")
        logger.info("="*60)
        
        # Analyze document relationships
        relationship_map = await self.mapper.analyze_document_relationships(
            user_id=self.demo_user_id,
            similarity_threshold=0.1,
            include_clusters=True
        )
        
        print(f"\n📊 ANALYSIS RESULTS:")
        print(f"   • Total Documents: {len(relationship_map.documents)}")
        print(f"   • Total Similarities Found: {len(relationship_map.similarities)}")
        print(f"   • Total Connections: {len(relationship_map.connections)}")
        print(f"   • Document Clusters: {len(relationship_map.clusters)}")
        
        # Display document similarities
        if relationship_map.similarities:
            print(f"\n🔗 TOP DOCUMENT SIMILARITIES:")
            for i, similarity in enumerate(relationship_map.similarities[:5], 1):
                print(f"   {i}. {similarity.document1_name} ↔ {similarity.document2_name}")
                print(f"      Type: {similarity.similarity_type.title()}")
                print(f"      Score: {similarity.similarity_score:.3f}")
                if similarity.shared_entities:
                    print(f"      Shared Entities: {', '.join(similarity.shared_entities[:3])}")
                if similarity.shared_tags:
                    print(f"      Shared Tags: {', '.join(similarity.shared_tags[:3])}")
                print()
        
        # Display document clusters
        if relationship_map.clusters:
            print(f"\n📚 DOCUMENT CLUSTERS:")
            for cluster in relationship_map.clusters:
                print(f"   • {cluster.cluster_name}")
                print(f"     Documents: {len(cluster.documents)}")
                print(f"     Key Topics: {', '.join(cluster.centroid_topics[:5])}")
                print(f"     Coherence: {cluster.coherence_score:.3f}")
                print()
        
        # Display network metrics
        if relationship_map.network_metrics:
            print(f"\n📈 NETWORK METRICS:")
            metrics = relationship_map.network_metrics
            print(f"   • Network Density: {metrics.get('network_density', 0):.3f}")
            print(f"   • Connected Components: {metrics.get('connected_components', 0)}")
            print(f"   • Largest Component Size: {metrics.get('largest_component_size', 0)}")
            
            if 'most_connected_document' in metrics:
                most_connected = metrics['most_connected_document']
                doc_name = next(
                    (doc.name for doc in relationship_map.documents if doc.id == most_connected['id']),
                    "Unknown"
                )
                print(f"   • Most Connected Document: {doc_name}")
                print(f"     Centrality Score: {most_connected['degree_centrality']:.3f}")
        
        return relationship_map
    
    async def demonstrate_specific_document_connections(self, document_id: str):
        """Demonstrate connections for a specific document"""
        logger.info(f"\n🔍 CONNECTIONS FOR DOCUMENT: {document_id}")
        
        connections = await self.mapper.get_document_connections(
            document_id=document_id,
            user_id=self.demo_user_id,
            max_connections=5
        )
        
        if connections:
            print(f"   Found {len(connections)} connections:")
            for i, conn in enumerate(connections, 1):
                other_doc_id = (
                    conn.target_document_id if conn.source_document_id == document_id 
                    else conn.source_document_id
                )
                
                # Get document name
                doc = self.db.query(Document).filter(Document.id == other_doc_id).first()
                doc_name = doc.name if doc else "Unknown Document"
                
                print(f"   {i}. → {doc_name}")
                print(f"      Connection Type: {conn.connection_type}")
                print(f"      Strength: {conn.strength:.3f}")
                
                if conn.metadata.get('shared_entities'):
                    entities = conn.metadata['shared_entities'][:3]
                    print(f"      Shared Entities: {', '.join(entities)}")
                
                if conn.metadata.get('shared_tags'):
                    tags = conn.metadata['shared_tags'][:3]
                    print(f"      Shared Tags: {', '.join(tags)}")
                print()
        else:
            print("   No connections found for this document.")
    
    async def demonstrate_relationship_insights(self):
        """Demonstrate relationship insights"""
        logger.info(f"\n💡 RELATIONSHIP INSIGHTS")
        
        insights = await self.mapper.get_relationship_insights(self.demo_user_id)
        
        print(f"   📊 Overview:")
        print(f"      • Total Documents: {insights.get('total_documents', 0)}")
        print(f"      • Total Connections: {insights.get('total_connections', 0)}")
        
        # Similarity distribution
        if insights.get('similarity_distribution'):
            print(f"\n   🔗 Similarity Types:")
            for sim_type, count in insights['similarity_distribution'].items():
                print(f"      • {sim_type.title()}: {count}")
        
        # Cluster analysis
        if insights.get('cluster_analysis'):
            cluster_info = insights['cluster_analysis']
            print(f"\n   📚 Cluster Analysis:")
            print(f"      • Total Clusters: {cluster_info.get('total_clusters', 0)}")
            print(f"      • Largest Cluster: {cluster_info.get('largest_cluster_size', 0)} documents")
            print(f"      • Average Cluster Size: {cluster_info.get('average_cluster_size', 0):.1f}")
        
        # Network insights
        if insights.get('network_insights'):
            network = insights['network_insights']
            print(f"\n   🌐 Network Properties:")
            print(f"      • Density: {network.get('network_density', 0):.3f}")
            print(f"      • Components: {network.get('connected_components', 0)}")
        
        # Recommendations
        if insights.get('recommendations'):
            print(f"\n   💡 Recommendations:")
            for i, rec in enumerate(insights['recommendations'], 1):
                print(f"      {i}. {rec}")
    
    async def demonstrate_visualization_data(self, relationship_map):
        """Demonstrate visualization data generation"""
        logger.info(f"\n🎨 VISUALIZATION DATA")
        
        viz_data = relationship_map.visualization_data
        
        if viz_data:
            print(f"   📊 Visualization Components:")
            print(f"      • Nodes: {len(viz_data.get('nodes', []))}")
            print(f"      • Edges: {len(viz_data.get('edges', []))}")
            print(f"      • Clusters: {len(viz_data.get('clusters', []))}")
            
            # Sample node data
            if viz_data.get('nodes'):
                print(f"\n   🔵 Sample Node Data:")
                sample_node = viz_data['nodes'][0]
                print(f"      • ID: {sample_node.get('id')}")
                print(f"      • Name: {sample_node.get('name')}")
                print(f"      • Size: {sample_node.get('size')}")
                print(f"      • Cluster: {sample_node.get('cluster_name', 'None')}")
            
            # Sample edge data
            if viz_data.get('edges'):
                print(f"\n   🔗 Sample Edge Data:")
                sample_edge = viz_data['edges'][0]
                print(f"      • Source: {sample_edge.get('source')}")
                print(f"      • Target: {sample_edge.get('target')}")
                print(f"      • Weight: {sample_edge.get('weight', 0):.3f}")
                print(f"      • Type: {sample_edge.get('type')}")
            
            # Layout suggestions
            if viz_data.get('layout_suggestions'):
                layout = viz_data['layout_suggestions']
                print(f"\n   🎯 Layout Suggestions:")
                print(f"      • Force Directed: {layout.get('force_directed', False)}")
                print(f"      • Cluster Layout: {layout.get('cluster_layout', False)}")
                print(f"      • Hierarchical: {layout.get('hierarchical', False)}")
    
    async def run_comprehensive_demo(self):
        """Run comprehensive document relationship mapping demo"""
        try:
            # Setup demo data
            await self.setup_demo_data()
            
            # Demonstrate relationship analysis
            relationship_map = await self.demonstrate_relationship_analysis()
            
            # Demonstrate specific document connections
            if relationship_map.documents:
                sample_doc = relationship_map.documents[0]
                await self.demonstrate_specific_document_connections(sample_doc.id)
            
            # Demonstrate relationship insights
            await self.demonstrate_relationship_insights()
            
            # Demonstrate visualization data
            await self.demonstrate_visualization_data(relationship_map)
            
            logger.info(f"\n✅ Document Relationship Mapping Demo completed successfully!")
            
        except Exception as e:
            logger.error(f"Demo failed: {str(e)}")
            raise
        finally:
            self.db.close()

async def main():
    """Main demo function"""
    demo = DocumentRelationshipDemo()
    await demo.run_comprehensive_demo()

if __name__ == "__main__":
    asyncio.run(main())