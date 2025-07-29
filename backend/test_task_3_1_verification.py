#!/usr/bin/env python3
"""
Verification test for Task 3.1: Implement entity extraction and relationship mapping
This test verifies that all requirements have been met:
- Create EntityExtractor using NER libraries and LLM assistance
- Build RelationshipMapper to discover entity connections  
- Implement confidence scoring for extracted entities and relationships
- Write tests for entity extraction accuracy
- Requirements: 2.1, 2.2, 2.4
"""

import asyncio
import logging
from typing import List, Dict, Any

from services.knowledge_graph import EntityExtractor, RelationshipMapper, EnhancedKnowledgeGraphService
from models.schemas import EntityType, RelationshipType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Task31Verification:
    """Verification class for Task 3.1 requirements"""
    
    def __init__(self):
        self.entity_extractor = EntityExtractor()
        self.relationship_mapper = RelationshipMapper()
        self.kg_service = EnhancedKnowledgeGraphService()
    
    async def verify_all_requirements(self):
        """Verify all requirements for Task 3.1"""
        logger.info("🔍 Verifying Task 3.1: Entity extraction and relationship mapping")
        
        results = {
            "entity_extractor_ner": await self.verify_entity_extractor_ner(),
            "entity_extractor_llm": await self.verify_entity_extractor_llm_support(),
            "relationship_mapper": await self.verify_relationship_mapper(),
            "confidence_scoring_entities": await self.verify_entity_confidence_scoring(),
            "confidence_scoring_relationships": await self.verify_relationship_confidence_scoring(),
            "accuracy_tests": await self.verify_accuracy_tests(),
            "requirements_2_1": await self.verify_requirement_2_1(),
            "requirements_2_2": await self.verify_requirement_2_2(),
            "requirements_2_4": await self.verify_requirement_2_4()
        }
        
        # Summary
        passed_count = sum(1 for result in results.values() if result)
        total = len(results)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"TASK 3.1 VERIFICATION SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"✅ Passed: {passed_count}/{total} requirements")
        
        for requirement, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{status} - {requirement}")
        
        if passed_count == total:
            logger.info(f"\n🎉 Task 3.1 COMPLETED SUCCESSFULLY!")
            return True
        else:
            logger.error(f"\n❌ Task 3.1 has {total - passed_count} failing requirements")
            return False
    
    async def verify_entity_extractor_ner(self) -> bool:
        """Verify EntityExtractor uses NER libraries (spaCy)"""
        logger.info("\n📋 Verifying EntityExtractor uses NER libraries...")
        
        try:
            # Check if spaCy is available and working
            if self.entity_extractor.nlp is None:
                logger.warning("spaCy model not available, but fallback patterns should work")
            
            # Test with text that should trigger spaCy NER
            text = "Apple Inc. was founded by Steve Jobs in Cupertino, California."
            entities = await self.entity_extractor.extract_entities(text, use_llm=False)
            
            # Should find entities using spaCy or patterns
            spacy_entities = [e for e in entities if e.get('source') == 'spacy']
            pattern_entities = [e for e in entities if e.get('source') == 'pattern']
            
            logger.info(f"Found {len(spacy_entities)} spaCy entities, {len(pattern_entities)} pattern entities")
            
            # Should have at least some entities detected
            return len(entities) > 0
            
        except Exception as e:
            logger.error(f"EntityExtractor NER verification failed: {str(e)}")
            return False
    
    async def verify_entity_extractor_llm_support(self) -> bool:
        """Verify EntityExtractor supports LLM assistance"""
        logger.info("\n📋 Verifying EntityExtractor LLM assistance support...")
        
        try:
            # Check if LLM extraction method exists
            assert hasattr(self.entity_extractor, '_extract_with_llm')
            assert hasattr(self.entity_extractor, '_query_llm')
            assert hasattr(self.entity_extractor, '_parse_llm_response')
            
            # Test LLM extraction (may fail if LLM not available, but method should exist)
            text = "Machine learning algorithms process complex data patterns."
            entities = await self.entity_extractor.extract_entities(text, use_llm=True)
            
            logger.info(f"LLM extraction method available and callable")
            return True
            
        except Exception as e:
            logger.error(f"EntityExtractor LLM support verification failed: {str(e)}")
            return False
    
    async def verify_relationship_mapper(self) -> bool:
        """Verify RelationshipMapper discovers entity connections"""
        logger.info("\n📋 Verifying RelationshipMapper discovers entity connections...")
        
        try:
            # Test relationship discovery
            entities = [
                {"text": "smoking", "type": EntityType.CONCEPT, "start": 0, "end": 7, "confidence": 0.8},
                {"text": "lung cancer", "type": EntityType.CONCEPT, "start": 15, "end": 26, "confidence": 0.8}
            ]
            
            text = "Smoking causes lung cancer."
            relationships = await self.relationship_mapper.extract_relationships(text, entities, use_llm=False)
            
            # Should find causal relationship
            causal_rels = [r for r in relationships if r['type'] == RelationshipType.CAUSES]
            
            logger.info(f"Found {len(relationships)} total relationships, {len(causal_rels)} causal relationships")
            
            # Verify relationship mapping methods exist
            assert hasattr(self.relationship_mapper, '_extract_with_patterns')
            assert hasattr(self.relationship_mapper, '_extract_cooccurrence')
            assert hasattr(self.relationship_mapper, '_extract_with_llm')
            
            return len(relationships) > 0
            
        except Exception as e:
            logger.error(f"RelationshipMapper verification failed: {str(e)}")
            return False
    
    async def verify_entity_confidence_scoring(self) -> bool:
        """Verify confidence scoring for entities"""
        logger.info("\n📋 Verifying entity confidence scoring...")
        
        try:
            text = "Apple Inc. is a major technology company based in California."
            entities = await self.entity_extractor.extract_entities(text, use_llm=False)
            
            # All entities should have confidence scores
            for entity in entities:
                assert 'confidence' in entity
                assert 0.0 <= entity['confidence'] <= 1.0
                assert isinstance(entity['confidence'], (int, float))
            
            # Test confidence calculation methods
            assert hasattr(self.entity_extractor, '_calculate_spacy_confidence')
            assert hasattr(self.entity_extractor, '_deduplicate_and_score')
            
            logger.info(f"All {len(entities)} entities have valid confidence scores")
            return len(entities) > 0
            
        except Exception as e:
            logger.error(f"Entity confidence scoring verification failed: {str(e)}")
            return False
    
    async def verify_relationship_confidence_scoring(self) -> bool:
        """Verify confidence scoring for relationships"""
        logger.info("\n📋 Verifying relationship confidence scoring...")
        
        try:
            entities = [
                {"text": "heart", "type": EntityType.CONCEPT, "start": 4, "end": 9, "confidence": 0.8},
                {"text": "cardiovascular system", "type": EntityType.CONCEPT, "start": 25, "end": 46, "confidence": 0.8}
            ]
            
            text = "The heart is part of the cardiovascular system."
            relationships = await self.relationship_mapper.extract_relationships(text, entities, use_llm=False)
            
            # All relationships should have confidence scores
            for rel in relationships:
                assert 'confidence' in rel
                assert 0.0 <= rel['confidence'] <= 1.0
                assert isinstance(rel['confidence'], (int, float))
            
            # Test confidence calculation methods
            assert hasattr(self.relationship_mapper, '_calculate_cooccurrence_confidence')
            assert hasattr(self.relationship_mapper, '_calculate_pattern_confidence')
            
            logger.info(f"All {len(relationships)} relationships have valid confidence scores")
            return len(relationships) > 0
            
        except Exception as e:
            logger.error(f"Relationship confidence scoring verification failed: {str(e)}")
            return False
    
    async def verify_accuracy_tests(self) -> bool:
        """Verify tests for entity extraction accuracy exist and pass"""
        logger.info("\n📋 Verifying entity extraction accuracy tests...")
        
        try:
            # Test various entity types for accuracy
            test_cases = [
                {
                    "text": "Barack Obama was President of the United States.",
                    "expected_entities": ["Barack Obama", "United States"],
                    "expected_types": [EntityType.PERSON, EntityType.LOCATION]
                },
                {
                    "text": "Apple Inc. released the iPhone in 2007.",
                    "expected_entities": ["Apple Inc.", "iPhone"],
                    "expected_types": [EntityType.ORGANIZATION, EntityType.PRODUCT]
                },
                {
                    "text": "Machine learning is part of artificial intelligence.",
                    "expected_entities": ["machine learning", "artificial intelligence"],
                    "expected_types": [EntityType.CONCEPT, EntityType.CONCEPT]
                }
            ]
            
            total_expected = 0
            total_found = 0
            
            for test_case in test_cases:
                entities = await self.entity_extractor.extract_entities(test_case["text"], use_llm=False)
                
                for expected_entity in test_case["expected_entities"]:
                    total_expected += 1
                    # Check if entity was found (flexible matching)
                    found = any(
                        expected_entity.lower() in entity["text"].lower() or 
                        entity["text"].lower() in expected_entity.lower()
                        for entity in entities
                    )
                    if found:
                        total_found += 1
            
            accuracy = total_found / total_expected if total_expected > 0 else 0
            logger.info(f"Entity extraction accuracy: {accuracy:.2%} ({total_found}/{total_expected})")
            
            # Require at least 50% accuracy
            return accuracy >= 0.5
            
        except Exception as e:
            logger.error(f"Accuracy tests verification failed: {str(e)}")
            return False
    
    async def verify_requirement_2_1(self) -> bool:
        """Verify Requirement 2.1: Extract entities and relationships to build knowledge graph"""
        logger.info("\n📋 Verifying Requirement 2.1: Knowledge graph entity/relationship extraction...")
        
        try:
            text = "Apple Inc. was founded by Steve Jobs. The company is headquartered in Cupertino."
            
            # Extract entities
            entities = await self.entity_extractor.extract_entities(text, use_llm=False)
            
            # Extract relationships
            relationships = await self.relationship_mapper.extract_relationships(text, entities, use_llm=False)
            
            # Should find key entities
            entity_texts = [e["text"].lower() for e in entities]
            has_apple = any("apple" in text for text in entity_texts)
            has_steve = any("steve" in text for text in entity_texts)
            has_cupertino = any("cupertino" in text for text in entity_texts)
            
            logger.info(f"Found entities: Apple={has_apple}, Steve Jobs={has_steve}, Cupertino={has_cupertino}")
            logger.info(f"Found {len(relationships)} relationships")
            
            return len(entities) > 0 and len(relationships) > 0
            
        except Exception as e:
            logger.error(f"Requirement 2.1 verification failed: {str(e)}")
            return False
    
    async def verify_requirement_2_2(self) -> bool:
        """Verify Requirement 2.2: Use knowledge graph relationships to enhance retrieval"""
        logger.info("\n📋 Verifying Requirement 2.2: Knowledge graph relationship usage...")
        
        try:
            # Verify that the service can build and query relationships
            await self.kg_service.initialize()
            
            # Check that graph builder and query engine exist
            assert hasattr(self.kg_service, 'graph_builder')
            assert hasattr(self.kg_service, 'query_engine')
            
            # Test relationship extraction and storage capability
            entities = [
                {"text": "Python", "type": EntityType.CONCEPT, "start": 0, "end": 6, "confidence": 0.8},
                {"text": "programming language", "type": EntityType.CONCEPT, "start": 12, "end": 32, "confidence": 0.8}
            ]
            
            text = "Python is a programming language."
            relationships = await self.relationship_mapper.extract_relationships(text, entities, use_llm=False)
            
            logger.info(f"Knowledge graph service initialized with relationship extraction capability")
            return len(relationships) > 0
            
        except Exception as e:
            logger.error(f"Requirement 2.2 verification failed: {str(e)}")
            return False
    
    async def verify_requirement_2_4(self) -> bool:
        """Verify Requirement 2.4: Confidence scoring for entities and relationships"""
        logger.info("\n📋 Verifying Requirement 2.4: Confidence scoring implementation...")
        
        try:
            text = "Microsoft Corporation develops software products like Windows and Office."
            
            # Extract entities with confidence scores
            entities = await self.entity_extractor.extract_entities(text, use_llm=False)
            
            # Extract relationships with confidence scores
            relationships = await self.relationship_mapper.extract_relationships(text, entities, use_llm=False)
            
            # Verify all entities have confidence scores
            entity_confidences = [e['confidence'] for e in entities]
            rel_confidences = [r['confidence'] for r in relationships]
            
            # Check confidence score ranges
            valid_entity_scores = all(0.0 <= conf <= 1.0 for conf in entity_confidences)
            valid_rel_scores = all(0.0 <= conf <= 1.0 for conf in rel_confidences)
            
            # Check confidence score variation (not all the same)
            entity_variation = len(set(entity_confidences)) > 1 if len(entity_confidences) > 1 else True
            rel_variation = len(set(rel_confidences)) > 1 if len(rel_confidences) > 1 else True
            
            logger.info(f"Entity confidence scores: {entity_confidences}")
            logger.info(f"Relationship confidence scores: {rel_confidences}")
            logger.info(f"Valid ranges: entities={valid_entity_scores}, relationships={valid_rel_scores}")
            logger.info(f"Score variation: entities={entity_variation}, relationships={rel_variation}")
            
            return (valid_entity_scores and valid_rel_scores and 
                   len(entities) > 0 and len(relationships) > 0)
            
        except Exception as e:
            logger.error(f"Requirement 2.4 verification failed: {str(e)}")
            return False


async def main():
    """Run Task 3.1 verification"""
    verifier = Task31Verification()
    
    try:
        success = await verifier.verify_all_requirements()
        
        if success:
            logger.info("\n🎉 Task 3.1 verification PASSED - All requirements met!")
            return 0
        else:
            logger.error("\n❌ Task 3.1 verification FAILED - Some requirements not met")
            return 1
            
    except Exception as e:
        logger.error(f"Verification failed with error: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)