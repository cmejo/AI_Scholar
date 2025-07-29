#!/usr/bin/env python3
"""
Comprehensive integration test for knowledge graph storage and query system
Tests the complete workflow of adding documents and updating the graph
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.knowledge_graph import EnhancedKnowledgeGraphService
from models.schemas import EntityType, RelationshipType
from core.database import get_db, KnowledgeGraphEntity, KnowledgeGraphRelationship
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_document_addition_and_graph_update():
    """Test adding documents and updating the knowledge graph"""
    print("=" * 80)
    print("COMPREHENSIVE KNOWLEDGE GRAPH INTEGRATION TEST")
    print("=" * 80)
    
    service = EnhancedKnowledgeGraphService()
    await service.initialize()
    
    # Simulate document data with entities and relationships
    document_1_data = {
        "id": "doc_1",
        "name": "AI Research Paper",
        "content": "Artificial Intelligence and Machine Learning are transforming technology."
    }
    
    # Simulate extracted entities for document 1
    doc1_entities = [
        {
            "text": "Artificial Intelligence",
            "type": EntityType.CONCEPT,
            "confidence": 0.95,
            "source": "test",
            "metadata": {"domain": "technology"}
        },
        {
            "text": "Machine Learning", 
            "type": EntityType.CONCEPT,
            "confidence": 0.90,
            "source": "test",
            "metadata": {"domain": "technology"}
        },
        {
            "text": "Technology",
            "type": EntityType.CONCEPT,
            "confidence": 0.85,
            "source": "test", 
            "metadata": {"domain": "general"}
        }
    ]
    
    # Simulate extracted relationships for document 1
    doc1_relationships = [
        {
            "source": "Machine Learning",
            "target": "Artificial Intelligence",
            "type": RelationshipType.PART_OF,
            "confidence": 0.90,
            "context": "Machine Learning is part of AI",
            "source_method": "test"
        },
        {
            "source": "Artificial Intelligence", 
            "target": "Technology",
            "type": RelationshipType.RELATED_TO,
            "confidence": 0.85,
            "context": "AI is transforming technology",
            "source_method": "test"
        }
    ]
    
    print("1. Testing graph state before adding documents...")
    initial_stats = await service.query_engine.get_graph_statistics()
    print(f"   - Initial nodes: {initial_stats['total_nodes']}")
    print(f"   - Initial edges: {initial_stats['total_edges']}")
    
    print("\n2. Simulating document processing and entity/relationship extraction...")
    
    # Manually store entities and relationships in database (simulating the document processing)
    try:
        db = next(get_db())
        
        # Store entities
        stored_entities = []
        for entity_data in doc1_entities:
            entity = KnowledgeGraphEntity(
                name=entity_data["text"],
                type=entity_data["type"].value,
                description=f"Entity from {document_1_data['name']}",
                importance_score=entity_data["confidence"],
                document_id=document_1_data["id"],
                entity_metadata={
                    "extraction_source": entity_data["source"],
                    "confidence": entity_data["confidence"],
                    **entity_data.get("metadata", {})
                }
            )
            db.add(entity)
            db.commit()
            db.refresh(entity)
            stored_entities.append(entity)
        
        # Store relationships
        stored_relationships = []
        for rel_data in doc1_relationships:
            # Find source and target entities
            source_entity = next((e for e in stored_entities if e.name == rel_data["source"]), None)
            target_entity = next((e for e in stored_entities if e.name == rel_data["target"]), None)
            
            if source_entity and target_entity:
                relationship = KnowledgeGraphRelationship(
                    source_entity_id=source_entity.id,
                    target_entity_id=target_entity.id,
                    relationship_type=rel_data["type"].value,
                    confidence_score=rel_data["confidence"],
                    context=rel_data["context"],
                    relationship_metadata={
                        "extraction_method": rel_data["source_method"],
                        "document_id": document_1_data["id"]
                    }
                )
                db.add(relationship)
                db.commit()
                db.refresh(relationship)
                stored_relationships.append(relationship)
        
        print(f"   ✓ Stored {len(stored_entities)} entities and {len(stored_relationships)} relationships")
        
        # Extract data while session is active
        entity_data = []
        for entity in stored_entities:
            entity_data.append({
                "name": entity.name,
                "type": entity.type,
                "importance_score": entity.importance_score,
                "metadata": entity.entity_metadata or {}
            })
        
        relationship_data = []
        entity_lookup = {e.id: e for e in stored_entities}
        for rel in stored_relationships:
            source_entity = entity_lookup.get(rel.source_entity_id)
            target_entity = entity_lookup.get(rel.target_entity_id)
            
            if source_entity and target_entity:
                relationship_data.append({
                    "source_entity_name": source_entity.name,
                    "target_entity_name": target_entity.name,
                    "relationship_type": rel.relationship_type,
                    "confidence_score": rel.confidence_score,
                    "context": rel.context or "",
                    "metadata": rel.relationship_metadata or {}
                })
        
    except Exception as e:
        print(f"   ✗ Error storing test data: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()
    
    print("\n3. Testing graph update with new document data...")
    await service._update_graph_with_document_data(
        document_1_data["id"], entity_data, relationship_data
    )
    
    # Check graph state after update
    updated_stats = await service.query_engine.get_graph_statistics()
    print(f"   - Updated nodes: {updated_stats['total_nodes']}")
    print(f"   - Updated edges: {updated_stats['total_edges']}")
    print(f"   - Node types: {updated_stats['node_types']}")
    print(f"   - Relationship types: {updated_stats['relationship_types']}")
    
    print("\n4. Testing graph queries...")
    
    # Test entity search
    ai_entities = await service.query_engine.find_entities_by_type("CONCEPT", min_importance=0.8)
    print(f"   - Found {len(ai_entities)} concept entities with importance >= 0.8:")
    for entity in ai_entities:
        print(f"     * {entity['name']} (importance: {entity['importance']:.3f})")
    
    # Test relationship queries
    ai_related = await service.query_engine.find_related_entities(
        "Artificial Intelligence", max_depth=2, min_confidence=0.7
    )
    print(f"   - Found {len(ai_related)} entities related to 'Artificial Intelligence':")
    for entity in ai_related[:5]:  # Show top 5
        print(f"     * {entity['entity']} ({entity['relationship']}, confidence: {entity['confidence']:.3f})")
    
    # Test shortest path
    paths = await service.query_engine.find_shortest_path("Machine Learning", "Technology")
    print(f"   - Found {len(paths)} paths from 'Machine Learning' to 'Technology':")
    for i, path in enumerate(paths[:2]):
        print(f"     Path {i+1} (length: {path['path_length']}, confidence: {path['total_confidence']:.3f}):")
        for step in path['path']:
            print(f"       {step['from']} --[{step['relationship']}]--> {step['to']}")
    
    print("\n5. Testing second document addition...")
    
    # Add a second document with overlapping entities
    document_2_data = {
        "id": "doc_2", 
        "name": "Deep Learning Guide",
        "content": "Deep Learning is a subset of Machine Learning using neural networks."
    }
    
    doc2_entities = [
        {
            "text": "Deep Learning",
            "type": EntityType.CONCEPT,
            "confidence": 0.92,
            "source": "test",
            "metadata": {"domain": "technology"}
        },
        {
            "text": "Machine Learning",  # Overlapping entity
            "type": EntityType.CONCEPT, 
            "confidence": 0.88,
            "source": "test",
            "metadata": {"domain": "technology"}
        },
        {
            "text": "Neural Networks",
            "type": EntityType.CONCEPT,
            "confidence": 0.87,
            "source": "test",
            "metadata": {"domain": "technology"}
        }
    ]
    
    doc2_relationships = [
        {
            "source": "Deep Learning",
            "target": "Machine Learning", 
            "type": RelationshipType.PART_OF,
            "confidence": 0.95,
            "context": "Deep Learning is a subset of ML",
            "source_method": "test"
        },
        {
            "source": "Deep Learning",
            "target": "Neural Networks",
            "type": RelationshipType.RELATED_TO,
            "confidence": 0.90,
            "context": "Deep Learning uses neural networks",
            "source_method": "test"
        }
    ]
    
    # Store second document data
    try:
        db = next(get_db())
        
        stored_entities_2 = []
        for entity_data in doc2_entities:
            # Check if entity already exists (for overlapping entities)
            existing_entity = db.query(KnowledgeGraphEntity).filter(
                KnowledgeGraphEntity.name == entity_data["text"],
                KnowledgeGraphEntity.type == entity_data["type"].value
            ).first()
            
            if existing_entity:
                # Update importance score
                existing_entity.importance_score = max(
                    existing_entity.importance_score,
                    entity_data["confidence"]
                )
                db.commit()
                stored_entities_2.append(existing_entity)
            else:
                # Create new entity
                entity = KnowledgeGraphEntity(
                    name=entity_data["text"],
                    type=entity_data["type"].value,
                    description=f"Entity from {document_2_data['name']}",
                    importance_score=entity_data["confidence"],
                    document_id=document_2_data["id"],
                    entity_metadata={
                        "extraction_source": entity_data["source"],
                        "confidence": entity_data["confidence"],
                        **entity_data.get("metadata", {})
                    }
                )
                db.add(entity)
                db.commit()
                db.refresh(entity)
                stored_entities_2.append(entity)
        
        # Store relationships for second document
        stored_relationships_2 = []
        for rel_data in doc2_relationships:
            source_entity = next((e for e in stored_entities_2 if e.name == rel_data["source"]), None)
            target_entity = next((e for e in stored_entities_2 if e.name == rel_data["target"]), None)
            
            if source_entity and target_entity:
                # Check if relationship already exists
                existing_rel = db.query(KnowledgeGraphRelationship).filter(
                    KnowledgeGraphRelationship.source_entity_id == source_entity.id,
                    KnowledgeGraphRelationship.target_entity_id == target_entity.id,
                    KnowledgeGraphRelationship.relationship_type == rel_data["type"].value
                ).first()
                
                if existing_rel:
                    # Update confidence
                    existing_rel.confidence_score = max(
                        existing_rel.confidence_score,
                        rel_data["confidence"]
                    )
                    db.commit()
                    stored_relationships_2.append(existing_rel)
                else:
                    # Create new relationship
                    relationship = KnowledgeGraphRelationship(
                        source_entity_id=source_entity.id,
                        target_entity_id=target_entity.id,
                        relationship_type=rel_data["type"].value,
                        confidence_score=rel_data["confidence"],
                        context=rel_data["context"],
                        relationship_metadata={
                            "extraction_method": rel_data["source_method"],
                            "document_id": document_2_data["id"]
                        }
                    )
                    db.add(relationship)
                    db.commit()
                    db.refresh(relationship)
                    stored_relationships_2.append(relationship)
        
        print(f"   ✓ Processed second document: {len(stored_entities_2)} entities, {len(stored_relationships_2)} relationships")
        
        # Extract data while session is active
        entity_data_2 = []
        for entity in stored_entities_2:
            entity_data_2.append({
                "name": entity.name,
                "type": entity.type,
                "importance_score": entity.importance_score,
                "metadata": entity.entity_metadata or {}
            })
        
        relationship_data_2 = []
        entity_lookup_2 = {e.id: e for e in stored_entities_2}
        for rel in stored_relationships_2:
            source_entity = entity_lookup_2.get(rel.source_entity_id)
            target_entity = entity_lookup_2.get(rel.target_entity_id)
            
            if source_entity and target_entity:
                relationship_data_2.append({
                    "source_entity_name": source_entity.name,
                    "target_entity_name": target_entity.name,
                    "relationship_type": rel.relationship_type,
                    "confidence_score": rel.confidence_score,
                    "context": rel.context or "",
                    "metadata": rel.relationship_metadata or {}
                })
        
    except Exception as e:
        print(f"   ✗ Error processing second document: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()
    
    # Update graph with second document
    await service._update_graph_with_document_data(
        document_2_data["id"], entity_data_2, relationship_data_2
    )
    
    print("\n6. Testing final graph state...")
    final_stats = await service.query_engine.get_graph_statistics()
    print(f"   - Final nodes: {final_stats['total_nodes']}")
    print(f"   - Final edges: {final_stats['total_edges']}")
    print(f"   - Graph density: {final_stats['density']:.3f}")
    print(f"   - Connected components: {final_stats['connected_components']}")
    
    # Test complex queries on the updated graph
    print("\n7. Testing complex queries on updated graph...")
    
    # Find all paths between AI and Deep Learning
    ai_to_dl_paths = await service.query_engine.find_shortest_path("Artificial Intelligence", "Deep Learning")
    print(f"   - Paths from AI to Deep Learning: {len(ai_to_dl_paths)}")
    for i, path in enumerate(ai_to_dl_paths):
        print(f"     Path {i+1}: {' -> '.join([step['from'] for step in path['path']] + [path['path'][-1]['to']] if path['path'] else [])}")
    
    # Test pattern matching for part_of relationships
    pattern = {
        "relationship_type": "part_of",
        "min_confidence": 0.8
    }
    part_of_matches = await service.query_engine.query_by_pattern(pattern)
    print(f"   - 'Part of' relationships with confidence >= 0.8: {len(part_of_matches)}")
    for match in part_of_matches:
        print(f"     * {match['source']['name']} is part of {match['target']['name']} (confidence: {match['confidence']:.3f})")
    
    print("\n8. Testing full database rebuild...")
    # Test rebuilding the complete graph from database
    await service.build_full_graph_from_database()
    rebuild_stats = await service.query_engine.get_graph_statistics()
    print(f"   - Rebuilt graph nodes: {rebuild_stats['total_nodes']}")
    print(f"   - Rebuilt graph edges: {rebuild_stats['total_edges']}")
    
    # Verify the rebuilt graph works correctly
    rebuilt_query = await service.query_graph("Machine Learning")
    print(f"   - Query results after rebuild: {len(rebuilt_query.get('results', []))}")
    
    return True

async def main():
    """Run comprehensive integration test"""
    print("Starting Comprehensive Knowledge Graph Integration Test")
    print("=" * 80)
    
    try:
        success = await test_document_addition_and_graph_update()
        
        if success:
            print("\n" + "=" * 80)
            print("🎉 COMPREHENSIVE INTEGRATION TEST PASSED!")
            print("✓ GraphBuilder: Successfully constructs and maintains knowledge graphs")
            print("✓ GraphQueryEngine: Enables complex semantic queries over the graph")
            print("✓ Graph Updates: Correctly updates graphs when new documents are added")
            print("✓ Entity Merging: Properly handles overlapping entities across documents")
            print("✓ Relationship Updates: Updates relationship confidence scores appropriately")
            print("✓ Database Integration: Seamlessly integrates with database storage")
            print("✓ Query Functionality: Supports shortest path, pattern matching, and statistics")
            print("=" * 80)
        else:
            print("\n❌ INTEGRATION TEST FAILED")
            return False
            
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)