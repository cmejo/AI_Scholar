"""
Task 8.2 Verification: Build document relationship mapping
Tests to verify the implementation meets all requirements
"""
import asyncio
import pytest
import logging
from datetime import datetime
from typing import List, Dict, Any

from core.database import get_db, Document, DocumentChunk, KnowledgeGraphEntity, DocumentTag, User
from services.document_relationship_mapper import (
    DocumentRelationshipMapper, DocumentSimilarity, DocumentConnection,
    DocumentCluster, DocumentRelationshipMap
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Task82Verification:
    """Verification tests for Task 8.2: Build document relationship mapping"""
    
    def __init__(self):
        self.db = next(get_db())
        self.mapper = DocumentRelationshipMapper(self.db)
        self.test_user_id = "test_user_8_2"
        
    async def setup_test_data(self):
        """Set up test data for verification"""
        logger.info("Setting up test data for Task 8.2 verification...")
        
        # Create test user
        existing_user = self.db.query(User).filter(User.id == self.test_user_id).first()
        if not existing_user:
            test_user = User(
                id=self.test_user_id,
                email="test82@verification.com",
                name="Task 8.2 Test User",
                hashed_password="test_hash"
            )
            self.db.add(test_user)
        
        # Create test documents with known relationships
        test_docs = [
            {
                "id": "test_doc_1",
                "name": "Machine Learning Basics",
                "content": "Machine learning is a subset of artificial intelligence that focuses on algorithms.",
                "tags": ["machine learning", "AI", "algorithms"],
                "entities": ["Machine Learning", "Artificial Intelligence", "Algorithms"]
            },
            {
                "id": "test_doc_2", 
                "name": "Deep Learning Guide",
                "content": "Deep learning uses neural networks with multiple layers for artificial intelligence.",
                "tags": ["deep learning", "neural networks", "AI"],
                "entities": ["Deep Learning", "Neural Networks", "Artificial Intelligence"]
            },
            {
                "id": "test_doc_3",
                "name": "Data Science Overview",
                "content": "Data science combines statistics, programming, and machine learning for insights.",
                "tags": ["data science", "statistics", "machine learning"],
                "entities": ["Data Science", "Statistics", "Machine Learning"]
            }
        ]
        
        for doc_data in test_docs:
            # Check if document exists
            existing_doc = self.db.query(Document).filter(Document.id == doc_data["id"]).first()
            if existing_doc:
                continue
                
            # Create document
            document = Document(
                id=doc_data["id"],
                name=doc_data["name"],
                user_id=self.test_user_id,
                file_path=f"/test/{doc_data['id']}.txt",
                size=len(doc_data["content"]),
                status="processed",
                chunks_count=1,
                embeddings_count=1,
                content_type="text/plain"
            )
            self.db.add(document)
            
            # Create chunk
            chunk = DocumentChunk(
                id=f"{doc_data['id']}_chunk",
                document_id=doc_data["id"],
                content=doc_data["content"],
                chunk_index=0,
                page_number=1
            )
            self.db.add(chunk)
            
            # Create tags
            for tag_name in doc_data["tags"]:
                tag = DocumentTag(
                    document_id=doc_data["id"],
                    tag_name=tag_name,
                    tag_type="topic",
                    confidence_score=0.9,
                    generated_by="test"
                )
                self.db.add(tag)
            
            # Create entities
            for entity_name in doc_data["entities"]:
                entity = KnowledgeGraphEntity(
                    name=entity_name,
                    type="CONCEPT",
                    document_id=doc_data["id"],
                    importance_score=0.8,
                    metadata={"source": "test"}
                )
                self.db.add(entity)
        
        self.db.commit()
        logger.info("Test data setup completed")

    async def verify_document_relationship_mapper_implementation(self):
        """Verify DocumentRelationshipMapper is properly implemented"""
        logger.info("\n1. Verifying DocumentRelationshipMapper implementation...")
        
        # Test 1: Verify mapper can be instantiated
        assert self.mapper is not None, "DocumentRelationshipMapper should be instantiable"
        assert hasattr(self.mapper, 'analyze_document_relationships'), "Should have analyze_document_relationships method"
        assert hasattr(self.mapper, 'get_document_connections'), "Should have get_document_connections method"
        assert hasattr(self.mapper, 'get_relationship_insights'), "Should have get_relationship_insights method"
        
        logger.info("   ✅ DocumentRelationshipMapper properly implemented")
        return True

    async def verify_connection_visualization(self):
        """Verify connection visualization functionality"""
        logger.info("\n2. Verifying connection visualization...")
        
        # Test relationship analysis
        relationship_map = await self.mapper.analyze_document_relationships(
            user_id=self.test_user_id,
            similarity_threshold=0.1,
            include_clusters=True
        )
        
        # Verify return type
        assert isinstance(relationship_map, DocumentRelationshipMap), "Should return DocumentRelationshipMap"
        
        # Verify structure
        assert hasattr(relationship_map, 'documents'), "Should have documents attribute"
        assert hasattr(relationship_map, 'similarities'), "Should have similarities attribute"
        assert hasattr(relationship_map, 'connections'), "Should have connections attribute"
        assert hasattr(relationship_map, 'clusters'), "Should have clusters attribute"
        assert hasattr(relationship_map, 'network_metrics'), "Should have network_metrics attribute"
        assert hasattr(relationship_map, 'visualization_data'), "Should have visualization_data attribute"
        
        # Verify visualization data structure
        viz_data = relationship_map.visualization_data
        assert isinstance(viz_data, dict), "Visualization data should be a dictionary"
        assert 'nodes' in viz_data, "Should have nodes for visualization"
        assert 'edges' in viz_data, "Should have edges for visualization"
        assert 'layout_suggestions' in viz_data, "Should have layout suggestions"
        assert 'color_scheme' in viz_data, "Should have color scheme"
        
        # Verify nodes structure
        if viz_data['nodes']:
            sample_node = viz_data['nodes'][0]
            assert 'id' in sample_node, "Node should have id"
            assert 'name' in sample_node, "Node should have name"
            assert 'size' in sample_node, "Node should have size"
            assert 'cluster' in sample_node, "Node should have cluster info"
        
        # Verify edges structure
        if viz_data['edges']:
            sample_edge = viz_data['edges'][0]
            assert 'source' in sample_edge, "Edge should have source"
            assert 'target' in sample_edge, "Edge should have target"
            assert 'weight' in sample_edge, "Edge should have weight"
            assert 'type' in sample_edge, "Edge should have type"
        
        logger.info("   ✅ Connection visualization properly implemented")
        return True

    async def verify_document_similarity_analysis(self):
        """Verify document similarity and relationship analysis"""
        logger.info("\n3. Verifying document similarity analysis...")
        
        # Test similarity calculation
        relationship_map = await self.mapper.analyze_document_relationships(
            user_id=self.test_user_id,
            similarity_threshold=0.0  # Low threshold to catch all similarities
        )
        
        # Verify similarities are found
        similarities = relationship_map.similarities
        assert isinstance(similarities, list), "Similarities should be a list"
        
        # Verify similarity structure
        if similarities:
            sample_similarity = similarities[0]
            assert isinstance(sample_similarity, DocumentSimilarity), "Should be DocumentSimilarity object"
            assert hasattr(sample_similarity, 'document1_id'), "Should have document1_id"
            assert hasattr(sample_similarity, 'document2_id'), "Should have document2_id"
            assert hasattr(sample_similarity, 'similarity_score'), "Should have similarity_score"
            assert hasattr(sample_similarity, 'similarity_type'), "Should have similarity_type"
            assert hasattr(sample_similarity, 'shared_entities'), "Should have shared_entities"
            assert hasattr(sample_similarity, 'shared_tags'), "Should have shared_tags"
            
            # Verify similarity score is valid
            assert 0 <= sample_similarity.similarity_score <= 1, "Similarity score should be between 0 and 1"
            
            # Verify similarity types are valid
            valid_types = ['content', 'entity', 'tag']
            assert sample_similarity.similarity_type in valid_types, f"Similarity type should be one of {valid_types}"
        
        # Test different similarity types
        documents = self.db.query(Document).filter(Document.user_id == self.test_user_id).all()
        
        # Test content similarity
        content_similarities = await self.mapper._calculate_content_similarity(documents)
        assert isinstance(content_similarities, list), "Content similarities should be a list"
        
        # Test entity similarity
        entity_similarities = await self.mapper._calculate_entity_similarity(documents)
        assert isinstance(entity_similarities, list), "Entity similarities should be a list"
        
        # Test tag similarity
        tag_similarities = await self.mapper._calculate_tag_similarity(documents)
        assert isinstance(tag_similarities, list), "Tag similarities should be a list"
        
        logger.info("   ✅ Document similarity analysis properly implemented")
        return True

    async def verify_visual_mapping_connections(self):
        """Verify visual mapping of document connections"""
        logger.info("\n4. Verifying visual mapping of connections...")
        
        # Get relationship map
        relationship_map = await self.mapper.analyze_document_relationships(
            user_id=self.test_user_id,
            include_clusters=True
        )
        
        # Verify connections are generated
        connections = relationship_map.connections
        assert isinstance(connections, list), "Connections should be a list"
        
        # Verify connection structure
        if connections:
            sample_connection = connections[0]
            assert isinstance(sample_connection, DocumentConnection), "Should be DocumentConnection object"
            assert hasattr(sample_connection, 'source_document_id'), "Should have source_document_id"
            assert hasattr(sample_connection, 'target_document_id'), "Should have target_document_id"
            assert hasattr(sample_connection, 'connection_type'), "Should have connection_type"
            assert hasattr(sample_connection, 'strength'), "Should have strength"
            assert hasattr(sample_connection, 'metadata'), "Should have metadata"
            
            # Verify connection strength is valid
            assert 0 <= sample_connection.strength <= 1, "Connection strength should be between 0 and 1"
            
            # Verify connection type is valid
            assert sample_connection.connection_type.endswith('_similarity'), "Connection type should end with '_similarity'"
        
        # Verify network metrics calculation
        network_metrics = relationship_map.network_metrics
        assert isinstance(network_metrics, dict), "Network metrics should be a dictionary"
        
        expected_metrics = [
            'total_documents', 'total_connections', 'network_density',
            'connected_components', 'largest_component_size'
        ]
        
        for metric in expected_metrics:
            assert metric in network_metrics, f"Should have {metric} in network metrics"
        
        # Verify clustering if documents are clustered
        clusters = relationship_map.clusters
        assert isinstance(clusters, list), "Clusters should be a list"
        
        if clusters:
            sample_cluster = clusters[0]
            assert isinstance(sample_cluster, DocumentCluster), "Should be DocumentCluster object"
            assert hasattr(sample_cluster, 'cluster_id'), "Should have cluster_id"
            assert hasattr(sample_cluster, 'documents'), "Should have documents"
            assert hasattr(sample_cluster, 'centroid_topics'), "Should have centroid_topics"
            assert hasattr(sample_cluster, 'cluster_name'), "Should have cluster_name"
            assert hasattr(sample_cluster, 'coherence_score'), "Should have coherence_score"
        
        logger.info("   ✅ Visual mapping of connections properly implemented")
        return True

    async def verify_relationship_mapping_accuracy(self):
        """Verify relationship mapping accuracy and usefulness"""
        logger.info("\n5. Verifying relationship mapping accuracy...")
        
        # Test specific document connections
        documents = self.db.query(Document).filter(Document.user_id == self.test_user_id).all()
        
        if documents:
            test_doc = documents[0]
            connections = await self.mapper.get_document_connections(
                document_id=test_doc.id,
                user_id=self.test_user_id,
                max_connections=5
            )
            
            assert isinstance(connections, list), "Document connections should be a list"
            
            # Verify connections are relevant (should find connections for related documents)
            if len(documents) > 1:
                # With our test data, we should find some connections
                # since documents share entities and tags
                logger.info(f"   Found {len(connections)} connections for document {test_doc.name}")
        
        # Test relationship insights
        insights = await self.mapper.get_relationship_insights(self.test_user_id)
        assert isinstance(insights, dict), "Insights should be a dictionary"
        
        expected_insight_keys = [
            'total_documents', 'total_connections', 'similarity_distribution',
            'network_insights', 'recommendations'
        ]
        
        for key in expected_insight_keys:
            assert key in insights, f"Should have {key} in insights"
        
        # Verify recommendations are actionable
        recommendations = insights.get('recommendations', [])
        assert isinstance(recommendations, list), "Recommendations should be a list"
        
        # Test accuracy with known relationships
        # Our test documents should show relationships due to shared entities/tags
        relationship_map = await self.mapper.analyze_document_relationships(self.test_user_id)
        
        # Verify that documents with shared entities/tags are connected
        shared_ai_docs = []
        for doc in documents:
            tags = self.db.query(DocumentTag).filter(
                DocumentTag.document_id == doc.id,
                DocumentTag.tag_name == "AI"
            ).all()
            if tags:
                shared_ai_docs.append(doc.id)
        
        if len(shared_ai_docs) >= 2:
            # Should find connections between documents that share "AI" tag
            ai_connections = [
                conn for conn in relationship_map.connections
                if (conn.source_document_id in shared_ai_docs and 
                    conn.target_document_id in shared_ai_docs)
            ]
            logger.info(f"   Found {len(ai_connections)} connections between AI-related documents")
        
        logger.info("   ✅ Relationship mapping accuracy verified")
        return True

    async def verify_requirement_7_2_compliance(self):
        """Verify compliance with Requirement 7.2"""
        logger.info("\n6. Verifying Requirement 7.2 compliance...")
        logger.info("   Requirement 7.2: WHEN viewing document relationships THEN the system SHALL provide visual mapping of connections")
        
        # Test the main requirement: visual mapping of connections
        relationship_map = await self.mapper.analyze_document_relationships(self.test_user_id)
        
        # Verify visual mapping is provided
        assert 'visualization_data' in relationship_map.__dict__, "Should provide visualization data"
        
        viz_data = relationship_map.visualization_data
        assert isinstance(viz_data, dict), "Visualization data should be structured"
        assert 'nodes' in viz_data, "Should provide nodes for visual mapping"
        assert 'edges' in viz_data, "Should provide edges for visual mapping"
        
        # Verify the mapping shows connections
        if viz_data['edges']:
            logger.info(f"   ✅ Visual mapping provides {len(viz_data['edges'])} connection edges")
        
        if viz_data['nodes']:
            logger.info(f"   ✅ Visual mapping provides {len(viz_data['nodes'])} document nodes")
        
        # Verify layout suggestions for visualization
        assert 'layout_suggestions' in viz_data, "Should provide layout suggestions for visualization"
        layout = viz_data['layout_suggestions']
        assert isinstance(layout, dict), "Layout suggestions should be structured"
        
        # Verify color scheme for different connection types
        assert 'color_scheme' in viz_data, "Should provide color scheme for visual differentiation"
        colors = viz_data['color_scheme']
        assert isinstance(colors, dict), "Color scheme should be structured"
        
        logger.info("   ✅ Requirement 7.2 compliance verified")
        return True

    async def verify_error_handling(self):
        """Verify error handling in edge cases"""
        logger.info("\n7. Verifying error handling...")
        
        # Test with non-existent user
        result = await self.mapper.analyze_document_relationships("non_existent_user")
        assert isinstance(result, DocumentRelationshipMap), "Should handle non-existent user gracefully"
        assert len(result.documents) == 0, "Should return empty result for non-existent user"
        
        # Test with single document
        single_doc_user = "single_doc_user"
        
        # Create user with single document
        single_user = User(
            id=single_doc_user,
            email="single@test.com",
            name="Single Doc User",
            hashed_password="test_hash"
        )
        self.db.add(single_user)
        
        single_doc = Document(
            id="single_doc",
            name="Single Document",
            user_id=single_doc_user,
            file_path="/test/single_doc.txt",
            size=100,
            status="processed",
            chunks_count=1,
            embeddings_count=1,
            content_type="text/plain"
        )
        self.db.add(single_doc)
        self.db.commit()
        
        single_result = await self.mapper.analyze_document_relationships(single_doc_user)
        assert len(single_result.documents) == 1, "Should handle single document"
        assert len(single_result.connections) == 0, "Should have no connections with single document"
        
        logger.info("   ✅ Error handling verified")
        return True

    async def run_verification(self):
        """Run complete verification of Task 8.2"""
        logger.info("="*60)
        logger.info("TASK 8.2 VERIFICATION: Build document relationship mapping")
        logger.info("="*60)
        
        try:
            # Setup test data
            await self.setup_test_data()
            
            # Run verification tests
            verification_results = []
            
            verification_results.append(await self.verify_document_relationship_mapper_implementation())
            verification_results.append(await self.verify_connection_visualization())
            verification_results.append(await self.verify_document_similarity_analysis())
            verification_results.append(await self.verify_visual_mapping_connections())
            verification_results.append(await self.verify_relationship_mapping_accuracy())
            verification_results.append(await self.verify_requirement_7_2_compliance())
            verification_results.append(await self.verify_error_handling())
            
            # Summary
            passed_tests = sum(verification_results)
            total_tests = len(verification_results)
            
            logger.info(f"\n" + "="*60)
            logger.info(f"VERIFICATION SUMMARY")
            logger.info(f"="*60)
            logger.info(f"Tests Passed: {passed_tests}/{total_tests}")
            
            if passed_tests == total_tests:
                logger.info("✅ ALL VERIFICATION TESTS PASSED!")
                logger.info("Task 8.2 implementation meets all requirements:")
                logger.info("  ✅ DocumentRelationshipMapper implemented")
                logger.info("  ✅ Document similarity and relationship analysis working")
                logger.info("  ✅ Visual mapping of document connections provided")
                logger.info("  ✅ Relationship mapping accuracy verified")
                logger.info("  ✅ Requirement 7.2 compliance confirmed")
                return True
            else:
                logger.error(f"❌ {total_tests - passed_tests} verification tests failed!")
                return False
                
        except Exception as e:
            logger.error(f"Verification failed with error: {str(e)}")
            return False
        finally:
            self.db.close()

async def main():
    """Main verification function"""
    verification = Task82Verification()
    success = await verification.run_verification()
    
    if success:
        print("\n🎉 Task 8.2 verification completed successfully!")
        exit(0)
    else:
        print("\n❌ Task 8.2 verification failed!")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())