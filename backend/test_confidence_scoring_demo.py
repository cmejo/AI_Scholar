#!/usr/bin/env python3
"""
Focused test for confidence scoring in entity extraction and relationship mapping
"""

import asyncio
import logging
from typing import List, Dict, Any

from services.knowledge_graph import EntityExtractor, RelationshipMapper
from models.schemas import EntityType, RelationshipType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConfidenceScoringTest:
    """Test confidence scoring mechanisms"""
    
    def __init__(self):
        self.entity_extractor = EntityExtractor()
        self.relationship_mapper = RelationshipMapper()
    
    async def test_entity_confidence_factors(self):
        """Test various factors that affect entity confidence scoring"""
        logger.info("Testing entity confidence scoring factors")
        
        test_cases = [
            {
                "name": "High confidence entities (proper nouns, organizations)",
                "text": "Apple Inc. is headquartered in Cupertino, California. Microsoft Corporation is based in Redmond, Washington.",
                "expected_high_confidence": ["Apple Inc.", "Microsoft Corporation", "Cupertino", "Redmond"]
            },
            {
                "name": "Medium confidence entities (common patterns)",
                "text": "Contact support@company.com or visit https://example.com for more information.",
                "expected_medium_confidence": ["support@company.com", "https://example.com"]
            },
            {
                "name": "Repeated entities (should boost confidence)",
                "text": "Apple announced new products. Apple's revenue increased. Apple is a technology company.",
                "expected_boosted": ["Apple"]
            },
            {
                "name": "Context-dependent entities",
                "text": "The President of the United States met with the Prime Minister of Canada in Washington.",
                "expected_entities": ["United States", "Canada", "Washington"]
            }
        ]
        
        for test_case in test_cases:
            print(f"\n🧪 {test_case['name']}")
            print(f"Text: {test_case['text']}")
            
            entities = await self.entity_extractor.extract_entities(test_case['text'], use_llm=False)
            
            print(f"Entities extracted: {len(entities)}")
            for entity in sorted(entities, key=lambda x: x['confidence'], reverse=True):
                confidence_level = "HIGH" if entity['confidence'] > 0.8 else "MEDIUM" if entity['confidence'] > 0.5 else "LOW"
                print(f"  - {entity['text']} ({entity['type'].value}) - {entity['confidence']:.3f} [{confidence_level}] (source: {entity['source']})")
    
    async def test_relationship_confidence_factors(self):
        """Test factors affecting relationship confidence scoring"""
        logger.info("\nTesting relationship confidence scoring factors")
        
        test_cases = [
            {
                "name": "Close proximity relationships",
                "text": "Steve Jobs founded Apple Inc.",
                "description": "Entities close together should have higher confidence"
            },
            {
                "name": "Pattern-based relationships",
                "text": "Smoking causes lung cancer. Exercise leads to better health.",
                "description": "Clear causal patterns should have high confidence"
            },
            {
                "name": "Same sentence relationships",
                "text": "Apple Inc. and Microsoft are technology companies.",
                "description": "Entities in same sentence should have higher confidence"
            },
            {
                "name": "Cross-sentence relationships",
                "text": "Apple Inc. is a technology company. The company was founded by Steve Jobs.",
                "description": "Cross-sentence relationships should have lower confidence"
            }
        ]
        
        for test_case in test_cases:
            print(f"\n🧪 {test_case['name']}")
            print(f"Description: {test_case['description']}")
            print(f"Text: {test_case['text']}")
            
            entities = await self.entity_extractor.extract_entities(test_case['text'], use_llm=False)
            relationships = await self.relationship_mapper.extract_relationships(
                test_case['text'], entities, use_llm=False
            )
            
            print(f"Relationships found: {len(relationships)}")
            for rel in sorted(relationships, key=lambda x: x['confidence'], reverse=True)[:5]:
                confidence_level = "HIGH" if rel['confidence'] > 0.7 else "MEDIUM" if rel['confidence'] > 0.4 else "LOW"
                distance = rel.get('metadata', {}).get('distance', 'N/A')
                print(f"  - {rel['source']} → {rel['target']} ({rel['type'].value}) - {rel['confidence']:.3f} [{confidence_level}] (distance: {distance})")
    
    async def test_confidence_calibration(self):
        """Test if confidence scores are well-calibrated"""
        logger.info("\nTesting confidence score calibration")
        
        # Test with known good and bad examples
        good_examples = [
            "Apple Inc. was founded by Steve Jobs in Cupertino, California.",
            "Microsoft Corporation is headquartered in Redmond, Washington.",
            "The President of the United States lives in the White House."
        ]
        
        poor_examples = [
            "The the the and and or or but but.",  # Nonsensical text
            "a b c d e f g h i j k l m n o p q r s t u v w x y z",  # Random letters
            "123 456 789 000 111 222 333 444 555 666 777 888 999"  # Numbers only
        ]
        
        print("\n📊 Good examples (should have higher confidence):")
        good_confidences = []
        for text in good_examples:
            entities = await self.entity_extractor.extract_entities(text, use_llm=False)
            if entities:
                avg_confidence = sum(e['confidence'] for e in entities) / len(entities)
                good_confidences.append(avg_confidence)
                print(f"  Text: {text[:50]}...")
                print(f"  Average confidence: {avg_confidence:.3f}")
        
        print("\n📊 Poor examples (should have lower confidence):")
        poor_confidences = []
        for text in poor_examples:
            entities = await self.entity_extractor.extract_entities(text, use_llm=False)
            if entities:
                avg_confidence = sum(e['confidence'] for e in entities) / len(entities)
                poor_confidences.append(avg_confidence)
                print(f"  Text: {text[:50]}...")
                print(f"  Average confidence: {avg_confidence:.3f}")
            else:
                print(f"  Text: {text[:50]}...")
                print(f"  No entities found (good!)")
        
        if good_confidences and poor_confidences:
            avg_good = sum(good_confidences) / len(good_confidences)
            avg_poor = sum(poor_confidences) / len(poor_confidences)
            print(f"\n📈 Calibration Results:")
            print(f"  Average confidence for good examples: {avg_good:.3f}")
            print(f"  Average confidence for poor examples: {avg_poor:.3f}")
            print(f"  Confidence separation: {avg_good - avg_poor:.3f}")
    
    async def test_entity_type_accuracy(self):
        """Test accuracy of entity type classification"""
        logger.info("\nTesting entity type classification accuracy")
        
        test_cases = [
            {
                "text": "Barack Obama was the President of the United States.",
                "expected_types": {"Barack Obama": EntityType.PERSON, "United States": EntityType.LOCATION}
            },
            {
                "text": "Apple Inc. released the iPhone in 2007.",
                "expected_types": {"Apple Inc.": EntityType.ORGANIZATION, "iPhone": EntityType.PRODUCT}
            },
            {
                "text": "The World War II ended in 1945.",
                "expected_types": {"World War II": EntityType.EVENT}
            },
            {
                "text": "Machine learning is a subset of artificial intelligence.",
                "expected_types": {"machine learning": EntityType.CONCEPT, "artificial intelligence": EntityType.CONCEPT}
            }
        ]
        
        correct_classifications = 0
        total_classifications = 0
        
        for test_case in test_cases:
            print(f"\nText: {test_case['text']}")
            entities = await self.entity_extractor.extract_entities(test_case['text'], use_llm=False)
            
            for entity in entities:
                entity_text_lower = entity['text'].lower()
                for expected_text, expected_type in test_case['expected_types'].items():
                    if expected_text.lower() in entity_text_lower or entity_text_lower in expected_text.lower():
                        total_classifications += 1
                        if entity['type'] == expected_type:
                            correct_classifications += 1
                            print(f"  ✅ {entity['text']} correctly classified as {entity['type'].value}")
                        else:
                            print(f"  ❌ {entity['text']} incorrectly classified as {entity['type'].value} (expected {expected_type.value})")
        
        if total_classifications > 0:
            accuracy = correct_classifications / total_classifications
            print(f"\n📊 Entity Type Classification Accuracy: {accuracy:.2%} ({correct_classifications}/{total_classifications})")
    
    async def test_relationship_type_accuracy(self):
        """Test accuracy of relationship type classification"""
        logger.info("\nTesting relationship type classification accuracy")
        
        test_cases = [
            {
                "text": "Smoking causes lung cancer.",
                "expected_relationships": [("smoking", "lung cancer", RelationshipType.CAUSES)]
            },
            {
                "text": "The heart is part of the cardiovascular system.",
                "expected_relationships": [("heart", "cardiovascular system", RelationshipType.PART_OF)]
            },
            {
                "text": "Dogs are similar to wolves.",
                "expected_relationships": [("dogs", "wolves", RelationshipType.SIMILAR_TO)]
            }
        ]
        
        for test_case in test_cases:
            print(f"\nText: {test_case['text']}")
            entities = await self.entity_extractor.extract_entities(test_case['text'], use_llm=False)
            relationships = await self.relationship_mapper.extract_relationships(
                test_case['text'], entities, use_llm=False
            )
            
            print(f"Found {len(relationships)} relationships:")
            for rel in relationships:
                print(f"  - {rel['source']} → {rel['target']} ({rel['type'].value}) - {rel['confidence']:.3f}")


async def main():
    """Run all confidence scoring tests"""
    tester = ConfidenceScoringTest()
    
    try:
        await tester.test_entity_confidence_factors()
        await tester.test_relationship_confidence_factors()
        await tester.test_confidence_calibration()
        await tester.test_entity_type_accuracy()
        await tester.test_relationship_type_accuracy()
        
        logger.info("\n✅ All confidence scoring tests completed!")
        
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())