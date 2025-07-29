#!/usr/bin/env python3
"""
Debug script for relationship pattern matching
"""

import asyncio
import re
from services.knowledge_graph import EntityExtractor, RelationshipMapper
from models.schemas import RelationshipType

async def debug_relationship_patterns():
    """Debug relationship pattern matching"""
    
    extractor = EntityExtractor()
    mapper = RelationshipMapper()
    
    test_cases = [
        "Smoking causes lung cancer.",
        "The heart is part of the cardiovascular system.",
        "Dogs are similar to wolves.",
        "Machine learning is a subset of artificial intelligence."
    ]
    
    for text in test_cases:
        print(f"\n{'='*60}")
        print(f"Testing: {text}")
        print(f"{'='*60}")
        
        # First, extract entities
        entities = await extractor.extract_entities(text, use_llm=False)
        print(f"Entities found: {len(entities)}")
        for entity in entities:
            print(f"  - '{entity['text']}' ({entity['type'].value}) - {entity['confidence']:.3f}")
        
        # Test pattern matching manually
        print(f"\nTesting patterns manually:")
        for rel_type, patterns in mapper.relationship_patterns.items():
            print(f"\n{rel_type.value} patterns:")
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    print(f"  Pattern: {pattern}")
                    print(f"  Match: '{match.group(0)}'")
                    print(f"  Source: '{match.group(1).strip()}'")
                    print(f"  Target: '{match.group(2).strip()}'")
        
        # Now test relationship extraction
        relationships = await mapper.extract_relationships(text, entities, use_llm=False)
        print(f"\nRelationships found: {len(relationships)}")
        for rel in relationships:
            print(f"  - {rel['source']} → {rel['target']} ({rel['type'].value}) - {rel['confidence']:.3f}")
        
        # Test with manually created entities if none found
        if not entities:
            print(f"\nTesting with manually created entities:")
            manual_entities = []
            words = text.replace('.', '').split()
            for i, word in enumerate(words):
                if len(word) > 3:  # Skip short words
                    manual_entities.append({
                        "text": word,
                        "type": "concept",
                        "start": i * 10,
                        "end": (i + 1) * 10,
                        "confidence": 0.8
                    })
            
            print(f"Manual entities: {[e['text'] for e in manual_entities]}")
            manual_relationships = await mapper.extract_relationships(text, manual_entities, use_llm=False)
            print(f"Manual relationships found: {len(manual_relationships)}")
            for rel in manual_relationships:
                print(f"  - {rel['source']} → {rel['target']} ({rel['type'].value}) - {rel['confidence']:.3f}")

if __name__ == "__main__":
    asyncio.run(debug_relationship_patterns())