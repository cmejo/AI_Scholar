#!/usr/bin/env python3
"""
Demo script to test entity extraction and relationship mapping functionality
"""
import asyncio
import logging
from services.knowledge_graph import EntityExtractor, RelationshipMapper, EnhancedKnowledgeGraphService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def demo_entity_extraction():
    """Demonstrate entity extraction capabilities"""
    print("=" * 60)
    print("ENTITY EXTRACTION DEMO")
    print("=" * 60)
    
    extractor = EntityExtractor()
    
    # Test texts with different types of entities
    test_texts = [
        "Apple Inc. was founded by Steve Jobs and Steve Wozniak in Cupertino, California in 1976.",
        "The iPhone is a revolutionary product that changed the smartphone industry.",
        "Contact support@apple.com or visit https://apple.com for more information.",
        "Machine learning and artificial intelligence are transforming technology.",
        "The COVID-19 pandemic caused significant disruptions to global supply chains."
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\nTest {i}: {text}")
        print("-" * 50)
        
        # Extract entities (without LLM to avoid external dependencies)
        entities = await extractor.extract_entities(text, use_llm=False)
        
        if entities:
            print(f"Found {len(entities)} entities:")
            for entity in entities:
                print(f"  • {entity['text']} ({entity['type'].value}) - Confidence: {entity['confidence']:.2f} - Source: {entity['source']}")
        else:
            print("  No entities found")

async def demo_relationship_extraction():
    """Demonstrate relationship extraction capabilities"""
    print("\n" + "=" * 60)
    print("RELATIONSHIP EXTRACTION DEMO")
    print("=" * 60)
    
    extractor = EntityExtractor()
    mapper = RelationshipMapper()
    
    # Test texts with clear relationships
    test_texts = [
        "Apple Inc. was founded by Steve Jobs in Cupertino, California.",
        "Smoking causes lung cancer and other serious health problems.",
        "The iPhone is part of Apple's product ecosystem.",
        "Machine learning is similar to artificial intelligence in many ways.",
        "Python is defined as a high-level programming language."
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\nTest {i}: {text}")
        print("-" * 50)
        
        # First extract entities
        entities = await extractor.extract_entities(text, use_llm=False)
        print(f"Entities: {[e['text'] for e in entities]}")
        
        # Then extract relationships
        relationships = await mapper.extract_relationships(text, entities, use_llm=False)
        
        if relationships:
            print(f"Found {len(relationships)} relationships:")
            for rel in relationships:
                print(f"  • {rel['source']} --[{rel['type'].value}]--> {rel['target']} (Confidence: {rel['confidence']:.2f})")
                if rel.get('context'):
                    print(f"    Context: \"{rel['context'][:100]}...\"")
        else:
            print("  No relationships found")

async def demo_knowledge_graph_service():
    """Demonstrate the enhanced knowledge graph service"""
    print("\n" + "=" * 60)
    print("KNOWLEDGE GRAPH SERVICE DEMO")
    print("=" * 60)
    
    service = EnhancedKnowledgeGraphService()
    await service.initialize()
    
    # Simulate document data
    document_data = {
        "id": "demo_doc_1",
        "name": "Technology Companies Demo",
        "content": "Apple Inc. was founded by Steve Jobs and Steve Wozniak in Cupertino, California. The company is known for innovative products like the iPhone and iPad. Google, another tech giant, was founded by Larry Page and Sergey Brin at Stanford University."
    }
    
    print(f"Processing document: {document_data['name']}")
    print(f"Content: {document_data['content']}")
    
    # Extract entities and relationships from the content
    extractor = EntityExtractor()
    mapper = RelationshipMapper()
    
    entities = await extractor.extract_entities(document_data['content'], use_llm=False)
    relationships = await mapper.extract_relationships(document_data['content'], entities, use_llm=False)
    
    print(f"\nExtracted {len(entities)} entities and {len(relationships)} relationships")
    
    # Display entities
    print("\nEntities:")
    for entity in entities:
        print(f"  • {entity['text']} ({entity['type'].value}) - Confidence: {entity['confidence']:.2f}")
    
    # Display relationships
    print("\nRelationships:")
    for rel in relationships:
        print(f"  • {rel['source']} --[{rel['type'].value}]--> {rel['target']} (Confidence: {rel['confidence']:.2f})")

async def demo_confidence_scoring():
    """Demonstrate confidence scoring for entities and relationships"""
    print("\n" + "=" * 60)
    print("CONFIDENCE SCORING DEMO")
    print("=" * 60)
    
    extractor = EntityExtractor()
    mapper = RelationshipMapper()
    
    # Text with entities of varying confidence levels
    text = "Apple Inc. is a major technology company. The CEO Tim Cook leads the organization. Some say AAPL stock is volatile."
    
    print(f"Text: {text}")
    print("-" * 50)
    
    entities = await extractor.extract_entities(text, use_llm=False)
    relationships = await mapper.extract_relationships(text, entities, use_llm=False)
    
    print("Entity Confidence Analysis:")
    for entity in sorted(entities, key=lambda x: x['confidence'], reverse=True):
        confidence_level = "High" if entity['confidence'] > 0.8 else "Medium" if entity['confidence'] > 0.5 else "Low"
        print(f"  • {entity['text']} - {entity['confidence']:.3f} ({confidence_level}) - {entity['source']}")
    
    if relationships:
        print("\nRelationship Confidence Analysis:")
        for rel in sorted(relationships, key=lambda x: x['confidence'], reverse=True):
            confidence_level = "High" if rel['confidence'] > 0.8 else "Medium" if rel['confidence'] > 0.5 else "Low"
            print(f"  • {rel['source']} → {rel['target']} - {rel['confidence']:.3f} ({confidence_level})")

async def main():
    """Run all demos"""
    print("Enhanced Knowledge Graph Entity Extraction and Relationship Mapping Demo")
    print("=" * 80)
    
    try:
        await demo_entity_extraction()
        await demo_relationship_extraction()
        await demo_knowledge_graph_service()
        await demo_confidence_scoring()
        
        print("\n" + "=" * 80)
        print("DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        
    except Exception as e:
        logger.error(f"Demo failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())