#!/usr/bin/env python3
"""
Comprehensive demo script for testing entity extraction and relationship mapping
This script demonstrates the enhanced knowledge graph capabilities.
"""

import asyncio
import json
import logging
from typing import List, Dict, Any

from services.knowledge_graph import EntityExtractor, RelationshipMapper, EnhancedKnowledgeGraphService
from models.schemas import EntityType, RelationshipType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EntityRelationshipDemo:
    """Demo class for testing entity extraction and relationship mapping"""
    
    def __init__(self):
        self.entity_extractor = EntityExtractor()
        self.relationship_mapper = RelationshipMapper()
        self.kg_service = EnhancedKnowledgeGraphService()
    
    async def run_comprehensive_demo(self):
        """Run comprehensive demo of entity extraction and relationship mapping"""
        logger.info("Starting comprehensive entity extraction and relationship mapping demo")
        
        # Test documents with different types of content
        test_documents = [
            {
                "title": "Technology Company Profile",
                "content": """
                Apple Inc. is an American multinational technology company headquartered in Cupertino, California. 
                The company was founded by Steve Jobs, Steve Wozniak, and Ronald Wayne in April 1976. 
                Apple is known for its innovative products including the iPhone, iPad, Mac computers, and Apple Watch.
                Tim Cook currently serves as the CEO of Apple Inc., having succeeded Steve Jobs in 2011.
                The company's headquarters, Apple Park, is located in Cupertino and houses over 12,000 employees.
                """
            },
            {
                "title": "Scientific Research Paper",
                "content": """
                Machine learning is a subset of artificial intelligence that enables computers to learn without explicit programming.
                Deep learning, a branch of machine learning, uses neural networks with multiple layers to model complex patterns.
                Convolutional Neural Networks (CNNs) are particularly effective for image recognition tasks.
                Researchers at Stanford University have developed new algorithms that improve the accuracy of CNNs.
                The research was published in Nature Machine Intelligence journal in 2023.
                """
            },
            {
                "title": "Historical Event",
                "content": """
                World War II was a global conflict that lasted from 1939 to 1945. The war involved most of the world's nations.
                Adolf Hitler led Nazi Germany during this period, while Winston Churchill served as Prime Minister of the United Kingdom.
                The United States entered the war after the attack on Pearl Harbor by Japan in December 1941.
                The war ended with the surrender of Germany in May 1945 and Japan in September 1945.
                """
            },
            {
                "title": "Medical Research",
                "content": """
                COVID-19 is caused by the SARS-CoV-2 virus, which was first identified in Wuhan, China in December 2019.
                The World Health Organization declared COVID-19 a pandemic in March 2020.
                Vaccines developed by Pfizer-BioNTech, Moderna, and Johnson & Johnson have proven effective against the virus.
                Dr. Anthony Fauci served as the chief medical advisor during the pandemic response in the United States.
                """
            }
        ]
        
        all_results = []
        
        for doc in test_documents:
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing: {doc['title']}")
            logger.info(f"{'='*60}")
            
            result = await self.process_document(doc['title'], doc['content'])
            all_results.append(result)
            
            # Display results
            await self.display_results(result)
        
        # Demonstrate cross-document analysis
        await self.demonstrate_cross_document_analysis(all_results)
        
        logger.info("\nDemo completed successfully!")
    
    async def process_document(self, title: str, content: str) -> Dict[str, Any]:
        """Process a single document for entity extraction and relationship mapping"""
        
        # Extract entities
        logger.info("Extracting entities...")
        entities = await self.entity_extractor.extract_entities(content, use_llm=False)
        
        # Extract relationships
        logger.info("Extracting relationships...")
        relationships = await self.relationship_mapper.extract_relationships(
            content, entities, use_llm=False
        )
        
        return {
            "title": title,
            "content": content,
            "entities": entities,
            "relationships": relationships,
            "stats": {
                "total_entities": len(entities),
                "total_relationships": len(relationships),
                "entity_types": self.count_entity_types(entities),
                "relationship_types": self.count_relationship_types(relationships)
            }
        }
    
    def count_entity_types(self, entities: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count entities by type"""
        type_counts = {}
        for entity in entities:
            entity_type = entity.get("type", EntityType.OTHER).value
            type_counts[entity_type] = type_counts.get(entity_type, 0) + 1
        return type_counts
    
    def count_relationship_types(self, relationships: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count relationships by type"""
        type_counts = {}
        for rel in relationships:
            rel_type = rel.get("type", RelationshipType.RELATED_TO).value
            type_counts[rel_type] = type_counts.get(rel_type, 0) + 1
        return type_counts
    
    async def display_results(self, result: Dict[str, Any]):
        """Display processing results in a formatted way"""
        
        print(f"\n📊 STATISTICS:")
        print(f"   Total Entities: {result['stats']['total_entities']}")
        print(f"   Total Relationships: {result['stats']['total_relationships']}")
        
        print(f"\n🏷️  ENTITY TYPES:")
        for entity_type, count in result['stats']['entity_types'].items():
            print(f"   {entity_type}: {count}")
        
        print(f"\n🔗 RELATIONSHIP TYPES:")
        for rel_type, count in result['stats']['relationship_types'].items():
            print(f"   {rel_type}: {count}")
        
        print(f"\n👥 TOP ENTITIES (by confidence):")
        top_entities = sorted(result['entities'], key=lambda x: x['confidence'], reverse=True)[:5]
        for i, entity in enumerate(top_entities, 1):
            print(f"   {i}. {entity['text']} ({entity['type'].value}) - {entity['confidence']:.2f}")
        
        print(f"\n🔗 TOP RELATIONSHIPS (by confidence):")
        top_relationships = sorted(result['relationships'], key=lambda x: x['confidence'], reverse=True)[:5]
        for i, rel in enumerate(top_relationships, 1):
            print(f"   {i}. {rel['source']} → {rel['target']} ({rel['type'].value}) - {rel['confidence']:.2f}")
    
    async def demonstrate_cross_document_analysis(self, results: List[Dict[str, Any]]):
        """Demonstrate analysis across multiple documents"""
        logger.info(f"\n{'='*60}")
        logger.info("CROSS-DOCUMENT ANALYSIS")
        logger.info(f"{'='*60}")
        
        # Collect all entities across documents
        all_entities = []
        all_relationships = []
        
        for result in results:
            all_entities.extend(result['entities'])
            all_relationships.extend(result['relationships'])
        
        # Find common entities across documents
        entity_names = [e['text'].lower() for e in all_entities]
        entity_counts = {}
        for name in entity_names:
            entity_counts[name] = entity_counts.get(name, 0) + 1
        
        common_entities = {name: count for name, count in entity_counts.items() if count > 1}
        
        print(f"\n🔄 ENTITIES APPEARING IN MULTIPLE DOCUMENTS:")
        for entity, count in sorted(common_entities.items(), key=lambda x: x[1], reverse=True):
            print(f"   {entity}: appears in {count} documents")
        
        # Analyze entity type distribution
        print(f"\n📈 OVERALL ENTITY TYPE DISTRIBUTION:")
        overall_type_counts = {}
        for entity in all_entities:
            entity_type = entity.get("type", EntityType.OTHER).value
            overall_type_counts[entity_type] = overall_type_counts.get(entity_type, 0) + 1
        
        for entity_type, count in sorted(overall_type_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   {entity_type}: {count}")
        
        # Analyze relationship patterns
        print(f"\n🔗 OVERALL RELATIONSHIP TYPE DISTRIBUTION:")
        overall_rel_counts = {}
        for rel in all_relationships:
            rel_type = rel.get("type", RelationshipType.RELATED_TO).value
            overall_rel_counts[rel_type] = overall_rel_counts.get(rel_type, 0) + 1
        
        for rel_type, count in sorted(overall_rel_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   {rel_type}: {count}")
        
        # Calculate average confidence scores
        avg_entity_confidence = sum(e['confidence'] for e in all_entities) / len(all_entities) if all_entities else 0
        avg_rel_confidence = sum(r['confidence'] for r in all_relationships) / len(all_relationships) if all_relationships else 0
        
        print(f"\n📊 CONFIDENCE SCORES:")
        print(f"   Average Entity Confidence: {avg_entity_confidence:.3f}")
        print(f"   Average Relationship Confidence: {avg_rel_confidence:.3f}")
    
    async def test_specific_scenarios(self):
        """Test specific scenarios for entity extraction and relationship mapping"""
        logger.info(f"\n{'='*60}")
        logger.info("TESTING SPECIFIC SCENARIOS")
        logger.info(f"{'='*60}")
        
        test_cases = [
            {
                "name": "Causal Relationships",
                "text": "Smoking causes lung cancer. Air pollution leads to respiratory problems. Exercise improves cardiovascular health."
            },
            {
                "name": "Hierarchical Relationships", 
                "text": "The heart is part of the cardiovascular system. The cardiovascular system belongs to the human body. Cells are components of tissues."
            },
            {
                "name": "Temporal Relationships",
                "text": "The Renaissance period preceded the Industrial Revolution. World War I occurred before World War II. The invention of the internet came after the development of computers."
            },
            {
                "name": "Technical Concepts",
                "text": "Machine learning algorithms use neural networks to process data. Deep learning is a subset of machine learning. Artificial intelligence encompasses both machine learning and expert systems."
            }
        ]
        
        for test_case in test_cases:
            print(f"\n🧪 Testing: {test_case['name']}")
            print(f"Text: {test_case['text']}")
            
            entities = await self.entity_extractor.extract_entities(test_case['text'], use_llm=False)
            relationships = await self.relationship_mapper.extract_relationships(
                test_case['text'], entities, use_llm=False
            )
            
            print(f"Entities found: {len(entities)}")
            for entity in entities:
                print(f"  - {entity['text']} ({entity['type'].value}, {entity['confidence']:.2f})")
            
            print(f"Relationships found: {len(relationships)}")
            for rel in relationships:
                print(f"  - {rel['source']} → {rel['target']} ({rel['type'].value}, {rel['confidence']:.2f})")


async def main():
    """Main function to run the demo"""
    demo = EntityRelationshipDemo()
    
    try:
        # Run comprehensive demo
        await demo.run_comprehensive_demo()
        
        # Test specific scenarios
        await demo.test_specific_scenarios()
        
    except Exception as e:
        logger.error(f"Demo failed with error: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())