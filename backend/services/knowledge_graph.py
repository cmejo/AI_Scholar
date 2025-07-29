"""
Enhanced Knowledge graph service for entity extraction and relationship mapping
"""
import networkx as nx
import json
import logging
import re
import asyncio
from typing import List, Dict, Any, Optional, Tuple, Set
import spacy
from collections import defaultdict, Counter
import requests
from datetime import datetime

from core.database import get_db, DocumentChunk, KnowledgeGraphEntity, KnowledgeGraphRelationship
from models.schemas import (
    KnowledgeGraphEntityCreate, KnowledgeGraphRelationshipCreate,
    EntityType, RelationshipType, ReasoningResult
)

logger = logging.getLogger(__name__)

class EntityExtractor:
    """Enhanced entity extraction using NER libraries and LLM assistance"""
    
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not found. Entity extraction will be limited.")
            self.nlp = None
        
        # Entity type mapping from spaCy to our schema
        self.entity_type_mapping = {
            "PERSON": EntityType.PERSON,
            "ORG": EntityType.ORGANIZATION,
            "GPE": EntityType.LOCATION,
            "LOC": EntityType.LOCATION,
            "EVENT": EntityType.EVENT,
            "PRODUCT": EntityType.PRODUCT,
            "WORK_OF_ART": EntityType.CONCEPT,
            "LAW": EntityType.CONCEPT,
            "LANGUAGE": EntityType.CONCEPT,
            "NORP": EntityType.CONCEPT,
            "FAC": EntityType.LOCATION,
            "MONEY": EntityType.CONCEPT,
            "PERCENT": EntityType.CONCEPT,
            "DATE": EntityType.CONCEPT,
            "TIME": EntityType.CONCEPT,
            "QUANTITY": EntityType.CONCEPT,
            "ORDINAL": EntityType.CONCEPT,
            "CARDINAL": EntityType.CONCEPT
        }
    
    async def extract_entities(self, text: str, use_llm: bool = True) -> List[Dict[str, Any]]:
        """Extract entities from text with confidence scoring"""
        entities = []
        
        # Primary extraction using spaCy
        if self.nlp:
            entities.extend(await self._extract_with_spacy(text))
        
        # Fallback pattern-based extraction
        entities.extend(await self._extract_with_patterns(text))
        
        # LLM-assisted extraction for complex entities
        if use_llm:
            llm_entities = await self._extract_with_llm(text)
            entities.extend(llm_entities)
        
        # Deduplicate and score entities
        return await self._deduplicate_and_score(entities, text)
    
    async def _extract_with_spacy(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities using spaCy NER"""
        entities = []
        doc = self.nlp(text)
        
        for ent in doc.ents:
            entity_type = self.entity_type_mapping.get(ent.label_, EntityType.OTHER)
            confidence = self._calculate_spacy_confidence(ent, doc)
            
            entities.append({
                "text": ent.text.strip(),
                "type": entity_type,
                "start": ent.start_char,
                "end": ent.end_char,
                "confidence": confidence,
                "source": "spacy",
                "metadata": {
                    "spacy_label": ent.label_,
                    "lemma": ent.lemma_,
                    "pos": ent.root.pos_
                }
            })
        
        return entities
    
    async def _extract_with_patterns(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities using pattern matching"""
        entities = []
        
        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        for match in re.finditer(email_pattern, text):
            entities.append({
                "text": match.group(),
                "type": EntityType.PERSON,
                "start": match.start(),
                "end": match.end(),
                "confidence": 0.9,
                "source": "pattern",
                "metadata": {"pattern_type": "email"}
            })
        
        # URL pattern
        url_pattern = r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?'
        for match in re.finditer(url_pattern, text):
            entities.append({
                "text": match.group(),
                "type": EntityType.CONCEPT,
                "start": match.start(),
                "end": match.end(),
                "confidence": 0.95,
                "source": "pattern",
                "metadata": {"pattern_type": "url"}
            })
        
        # Capitalized phrases (potential proper nouns)
        proper_noun_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        for match in re.finditer(proper_noun_pattern, text):
            # Skip if it's at the beginning of a sentence
            if match.start() == 0 or text[match.start()-1] in '.!?':
                continue
                
            entities.append({
                "text": match.group(),
                "type": EntityType.OTHER,
                "start": match.start(),
                "end": match.end(),
                "confidence": 0.6,
                "source": "pattern",
                "metadata": {"pattern_type": "proper_noun"}
            })
        
        # Medical/Scientific terms
        medical_pattern = r'\b(?:cancer|disease|virus|bacteria|infection|syndrome|disorder|condition|treatment|therapy|medicine|drug|vaccine|symptom|diagnosis)\b'
        for match in re.finditer(medical_pattern, text, re.IGNORECASE):
            entities.append({
                "text": match.group(),
                "type": EntityType.CONCEPT,
                "start": match.start(),
                "end": match.end(),
                "confidence": 0.8,
                "source": "pattern",
                "metadata": {"pattern_type": "medical_term"}
            })
        
        # Body parts and biological terms
        biological_pattern = r'\b(?:heart|brain|lung|liver|kidney|stomach|muscle|bone|blood|cell|tissue|organ|system|cardiovascular|respiratory|nervous|digestive)\b'
        for match in re.finditer(biological_pattern, text, re.IGNORECASE):
            entities.append({
                "text": match.group(),
                "type": EntityType.CONCEPT,
                "start": match.start(),
                "end": match.end(),
                "confidence": 0.8,
                "source": "pattern",
                "metadata": {"pattern_type": "biological_term"}
            })
        
        # Technology terms
        tech_pattern = r'\b(?:machine learning|artificial intelligence|neural network|algorithm|computer|software|hardware|internet|database|programming|technology|digital|cyber|AI|ML|API|CPU|GPU|RAM|SSD)\b'
        for match in re.finditer(tech_pattern, text, re.IGNORECASE):
            entities.append({
                "text": match.group(),
                "type": EntityType.CONCEPT,
                "start": match.start(),
                "end": match.end(),
                "confidence": 0.85,
                "source": "pattern",
                "metadata": {"pattern_type": "tech_term"}
            })
        
        # Animals
        animal_pattern = r'\b(?:dogs?|cats?|wolv(?:es?)|lions?|tigers?|elephants?|bears?|horses?|cows?|pigs?|sheep|goats?|chickens?|birds?|fish(?:es)?|whales?|dolphins?|sharks?|snakes?|spiders?|insects?|animals?|mammals?|reptiles?|amphibians?)\b'
        for match in re.finditer(animal_pattern, text, re.IGNORECASE):
            entities.append({
                "text": match.group(),
                "type": EntityType.CONCEPT,
                "start": match.start(),
                "end": match.end(),
                "confidence": 0.75,
                "source": "pattern",
                "metadata": {"pattern_type": "animal"}
            })
        
        # Activities and behaviors
        activity_pattern = r'\b(?:smoking|drinking|exercise|running|walking|swimming|eating|sleeping|working|studying|reading|writing|playing|dancing|singing)\b'
        for match in re.finditer(activity_pattern, text, re.IGNORECASE):
            entities.append({
                "text": match.group(),
                "type": EntityType.CONCEPT,
                "start": match.start(),
                "end": match.end(),
                "confidence": 0.7,
                "source": "pattern",
                "metadata": {"pattern_type": "activity"}
            })
        
        # Compound terms (two or more words that might be concepts)
        compound_pattern = r'\b(?:[a-z]+\s+(?:learning|intelligence|system|network|cancer|disease|syndrome|disorder))\b'
        for match in re.finditer(compound_pattern, text, re.IGNORECASE):
            entities.append({
                "text": match.group(),
                "type": EntityType.CONCEPT,
                "start": match.start(),
                "end": match.end(),
                "confidence": 0.8,
                "source": "pattern",
                "metadata": {"pattern_type": "compound_concept"}
            })
        
        return entities
    
    async def _extract_with_llm(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities using LLM assistance"""
        entities = []
        
        try:
            # Prepare prompt for LLM
            prompt = f"""
            Extract entities from the following text. Focus on:
            - Technical concepts and terminology
            - Domain-specific entities
            - Abstract concepts
            - Relationships and processes
            
            Text: {text[:1000]}  # Limit text length
            
            Return entities in JSON format with: name, type (person/organization/location/concept/event/product/other), confidence (0-1)
            """
            
            # Make request to local LLM (assuming Ollama is available)
            response = await self._query_llm(prompt)
            if response:
                llm_entities = self._parse_llm_response(response, text)
                entities.extend(llm_entities)
                
        except Exception as e:
            logger.warning(f"LLM entity extraction failed: {str(e)}")
        
        return entities
    
    async def _query_llm(self, prompt: str) -> Optional[str]:
        """Query local LLM for entity extraction"""
        try:
            # Assuming Ollama is running locally
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama2",  # or whatever model is available
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get("response", "")
        except Exception as e:
            logger.warning(f"LLM query failed: {str(e)}")
        
        return None
    
    def _parse_llm_response(self, response: str, original_text: str) -> List[Dict[str, Any]]:
        """Parse LLM response to extract entities"""
        entities = []
        
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                entity_data = json.loads(json_match.group())
                
                for item in entity_data:
                    if isinstance(item, dict) and "name" in item:
                        # Find entity position in original text
                        entity_text = item["name"]
                        start_pos = original_text.lower().find(entity_text.lower())
                        
                        if start_pos != -1:
                            entities.append({
                                "text": entity_text,
                                "type": self._map_llm_type(item.get("type", "other")),
                                "start": start_pos,
                                "end": start_pos + len(entity_text),
                                "confidence": float(item.get("confidence", 0.7)),
                                "source": "llm",
                                "metadata": {"llm_type": item.get("type")}
                            })
        except Exception as e:
            logger.warning(f"Failed to parse LLM response: {str(e)}")
        
        return entities
    
    def _map_llm_type(self, llm_type: str) -> EntityType:
        """Map LLM entity type to our schema"""
        type_mapping = {
            "person": EntityType.PERSON,
            "organization": EntityType.ORGANIZATION,
            "location": EntityType.LOCATION,
            "concept": EntityType.CONCEPT,
            "event": EntityType.EVENT,
            "product": EntityType.PRODUCT
        }
        return type_mapping.get(llm_type.lower(), EntityType.OTHER)
    
    def _calculate_spacy_confidence(self, ent, doc) -> float:
        """Calculate confidence score for spaCy entities"""
        base_confidence = 0.8
        
        # Adjust based on entity length
        if len(ent.text) < 3:
            base_confidence -= 0.2
        elif len(ent.text) > 20:
            base_confidence -= 0.1
        
        # Adjust based on context
        if ent.label_ in ["PERSON", "ORG", "GPE"]:
            base_confidence += 0.1
        
        # Check if entity appears multiple times
        entity_count = sum(1 for e in doc.ents if e.text.lower() == ent.text.lower())
        if entity_count > 1:
            base_confidence += 0.1
        
        return min(1.0, max(0.1, base_confidence))
    
    async def _deduplicate_and_score(self, entities: List[Dict[str, Any]], text: str) -> List[Dict[str, Any]]:
        """Deduplicate entities and calculate final confidence scores"""
        entity_groups = defaultdict(list)
        
        # Group similar entities
        for entity in entities:
            key = entity["text"].lower().strip()
            entity_groups[key].append(entity)
        
        final_entities = []
        for entity_group in entity_groups.values():
            if len(entity_group) == 1:
                final_entities.append(entity_group[0])
            else:
                # Merge entities with same text
                merged_entity = await self._merge_entities(entity_group, text)
                final_entities.append(merged_entity)
        
        return final_entities
    
    async def _merge_entities(self, entities: List[Dict[str, Any]], text: str) -> Dict[str, Any]:
        """Merge duplicate entities and calculate combined confidence"""
        # Use the entity with highest confidence as base
        base_entity = max(entities, key=lambda x: x["confidence"])
        
        # Calculate combined confidence
        confidences = [e["confidence"] for e in entities]
        sources = [e["source"] for e in entities]
        
        # Boost confidence if multiple sources agree
        combined_confidence = max(confidences)
        if len(set(sources)) > 1:
            combined_confidence = min(1.0, combined_confidence + 0.2)
        
        # Merge metadata
        merged_metadata = {}
        for entity in entities:
            merged_metadata.update(entity.get("metadata", {}))
        
        return {
            "text": base_entity["text"],
            "type": base_entity["type"],
            "start": base_entity["start"],
            "end": base_entity["end"],
            "confidence": combined_confidence,
            "source": "merged",
            "metadata": {
                **merged_metadata,
                "sources": sources,
                "merge_count": len(entities)
            }
        }


class RelationshipMapper:
    """Discover entity connections and relationships"""
    
    def __init__(self):
        # Enhanced relationship patterns for different types
        self.relationship_patterns = {
            RelationshipType.CAUSES: [
                r"(.+?)\s+(?:causes?|leads? to|results? in|triggers?|brings about|produces?)\s+(.+)",
                r"(.+?)\s+(?:because of|due to|owing to|as a result of)\s+(.+)",
                r"(.+?)\s+(?:→|->|leads to|results in)\s+(.+)",
                r"(.+?)\s+(?:makes?|creates?|generates?)\s+(.+)",
            ],
            RelationshipType.PART_OF: [
                r"(.+?)\s+(?:is part of|belongs to|is in|is within|is a component of)\s+(.+)",
                r"(.+?)\s+(?:contains?|includes?|has|comprises?|consists of)\s+(.+)",
                r"(.+?)\s+(?:is a member of|is included in)\s+(.+)",
            ],
            RelationshipType.SIMILAR_TO: [
                r"(.+?)\s+(?:(?:is|are)\s+similar to|(?:is|are)\s+like|resembles?|(?:is|are)\s+comparable to)\s+(.+)",
                r"(.+?)\s+(?:and|&)\s+(.+?)\s+(?:are similar|are alike|are comparable)",
                r"(.+?)\s+(?:mirrors?|parallels?|echoes?)\s+(.+)",
            ],
            RelationshipType.DEFINED_BY: [
                r"(.+?)\s+(?:is defined as|means|refers to|is|are)\s+(.+)",
                r"(.+?):\s+(.+)",  # Definition pattern
                r"(.+?)\s+(?:equals?|represents?|signifies?)\s+(.+)",
            ],
            RelationshipType.OPPOSITE_OF: [
                r"(.+?)\s+(?:is opposite to|opposes?|contrasts with|differs from)\s+(.+)",
                r"(.+?)\s+(?:vs\.?|versus|against)\s+(.+)",
                r"(.+?)\s+(?:but|however|while)\s+(.+)",
            ],
            RelationshipType.EXAMPLE_OF: [
                r"(.+?)\s+(?:is an example of|exemplifies?|illustrates?)\s+(.+)",
                r"(.+?)\s+(?:such as|like|including)\s+(.+)",
                r"(.+?)\s+(?:for example|for instance)\s+(.+)",
            ]
        }
    
    async def extract_relationships(
        self, 
        text: str, 
        entities: List[Dict[str, Any]], 
        use_llm: bool = True
    ) -> List[Dict[str, Any]]:
        """Extract relationships between entities"""
        relationships = []
        
        # Pattern-based relationship extraction
        relationships.extend(await self._extract_with_patterns(text, entities))
        
        # Co-occurrence based relationships
        relationships.extend(await self._extract_cooccurrence(text, entities))
        
        # LLM-assisted relationship extraction
        if use_llm:
            llm_relationships = await self._extract_with_llm(text, entities)
            relationships.extend(llm_relationships)
        
        # Score and filter relationships
        return await self._score_and_filter_relationships(relationships, text)
    
    async def _extract_with_patterns(self, text: str, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract relationships using pattern matching"""
        relationships = []
        entity_texts = [e["text"] for e in entities]
        
        # Split text into sentences for better pattern matching
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            for rel_type, patterns in self.relationship_patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, sentence, re.IGNORECASE)
                    
                    for match in matches:
                        source_text = match.group(1).strip()
                        target_text = match.group(2).strip()
                        
                        # Clean up the extracted text
                        source_text = self._clean_extracted_text(source_text)
                        target_text = self._clean_extracted_text(target_text)
                        
                        # Find matching entities (more flexible matching)
                        source_entity = self._find_matching_entity_flexible(source_text, entity_texts)
                        target_entity = self._find_matching_entity_flexible(target_text, entity_texts)
                        
                        if source_entity and target_entity and source_entity != target_entity:
                            # Calculate confidence based on pattern quality and match quality
                            confidence = self._calculate_pattern_confidence(
                                rel_type, pattern, match.group(0), source_entity, target_entity
                            )
                            
                            relationships.append({
                                "source": source_entity,
                                "target": target_entity,
                                "type": rel_type,
                                "confidence": confidence,
                                "context": match.group(0),
                                "source_method": "pattern",
                                "metadata": {
                                    "pattern": pattern,
                                    "sentence": sentence,
                                    "match_quality": "exact" if source_text in entity_texts and target_text in entity_texts else "partial"
                                }
                            })
        
        return relationships
    
    def _clean_extracted_text(self, text: str) -> str:
        """Clean extracted text from patterns"""
        # Remove common articles and prepositions from the beginning
        text = re.sub(r'^(?:the|a|an|this|that|these|those)\s+', '', text, flags=re.IGNORECASE)
        # Remove trailing punctuation
        text = re.sub(r'[,;:]+$', '', text)
        return text.strip()
    
    def _find_matching_entity_flexible(self, text: str, entity_texts: List[str]) -> Optional[str]:
        """Find entity with more flexible matching"""
        text_lower = text.lower().strip()
        
        # Exact match first
        for entity_text in entity_texts:
            if entity_text.lower() == text_lower:
                return entity_text
        
        # Partial match - entity contains the text
        for entity_text in entity_texts:
            if text_lower in entity_text.lower():
                return entity_text
        
        # Partial match - text contains the entity
        for entity_text in entity_texts:
            if entity_text.lower() in text_lower:
                return entity_text
        
        # Word-based matching for compound entities
        text_words = set(text_lower.split())
        for entity_text in entity_texts:
            entity_words = set(entity_text.lower().split())
            # If there's significant word overlap
            if len(text_words & entity_words) >= min(len(text_words), len(entity_words)) * 0.5:
                return entity_text
        
        return None
    
    def _calculate_pattern_confidence(
        self, 
        rel_type: RelationshipType, 
        pattern: str, 
        match_text: str, 
        source_entity: str, 
        target_entity: str
    ) -> float:
        """Calculate confidence for pattern-based relationships"""
        base_confidence = 0.8
        
        # Adjust based on relationship type (some patterns are more reliable)
        type_confidence_map = {
            RelationshipType.CAUSES: 0.9,
            RelationshipType.PART_OF: 0.85,
            RelationshipType.DEFINED_BY: 0.9,
            RelationshipType.SIMILAR_TO: 0.75,
            RelationshipType.OPPOSITE_OF: 0.8,
            RelationshipType.EXAMPLE_OF: 0.8
        }
        
        base_confidence = type_confidence_map.get(rel_type, 0.7)
        
        # Adjust based on match quality
        if source_entity.lower() in match_text.lower() and target_entity.lower() in match_text.lower():
            base_confidence += 0.1
        
        # Adjust based on entity quality (longer entities are often more specific)
        if len(source_entity) > 10 or len(target_entity) > 10:
            base_confidence += 0.05
        
        return min(1.0, base_confidence)
    
    async def _extract_cooccurrence(self, text: str, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract relationships based on entity co-occurrence"""
        relationships = []
        
        # Sort entities by position
        sorted_entities = sorted(entities, key=lambda x: x["start"])
        
        for i, entity1 in enumerate(sorted_entities):
            for entity2 in sorted_entities[i+1:]:
                distance = entity2["start"] - entity1["end"]
                
                # Only consider entities within reasonable distance
                if distance < 200:  # Within 200 characters
                    confidence = self._calculate_cooccurrence_confidence(
                        entity1, entity2, distance, text
                    )
                    
                    if confidence > 0.3:  # Minimum threshold
                        relationships.append({
                            "source": entity1["text"],
                            "target": entity2["text"],
                            "type": RelationshipType.RELATED_TO,
                            "confidence": confidence,
                            "context": text[entity1["start"]:entity2["end"]],
                            "source_method": "cooccurrence",
                            "metadata": {
                                "distance": distance,
                                "sentence_boundary": self._crosses_sentence_boundary(
                                    entity1, entity2, text
                                )
                            }
                        })
        
        return relationships
    
    def _calculate_cooccurrence_confidence(
        self, 
        entity1: Dict[str, Any], 
        entity2: Dict[str, Any], 
        distance: int, 
        text: str
    ) -> float:
        """Calculate confidence for co-occurrence relationships"""
        base_confidence = 0.5
        
        # Closer entities have higher confidence
        distance_factor = max(0.1, 1.0 - distance / 200)
        base_confidence *= distance_factor
        
        # Same sentence increases confidence
        if not self._crosses_sentence_boundary(entity1, entity2, text):
            base_confidence += 0.2
        
        # Entity types influence confidence
        type_bonus = self._get_type_relationship_bonus(entity1, entity2)
        base_confidence += type_bonus
        
        return min(1.0, base_confidence)
    
    def _crosses_sentence_boundary(
        self, 
        entity1: Dict[str, Any], 
        entity2: Dict[str, Any], 
        text: str
    ) -> bool:
        """Check if entities cross sentence boundaries"""
        between_text = text[entity1["end"]:entity2["start"]]
        return any(punct in between_text for punct in '.!?')
    
    def _get_type_relationship_bonus(
        self, 
        entity1: Dict[str, Any], 
        entity2: Dict[str, Any]
    ) -> float:
        """Get bonus based on entity type combinations"""
        type1 = entity1.get("type", EntityType.OTHER)
        type2 = entity2.get("type", EntityType.OTHER)
        
        # High-value type combinations
        high_value_pairs = [
            (EntityType.PERSON, EntityType.ORGANIZATION),
            (EntityType.PERSON, EntityType.LOCATION),
            (EntityType.ORGANIZATION, EntityType.LOCATION),
            (EntityType.CONCEPT, EntityType.PERSON),
            (EntityType.EVENT, EntityType.LOCATION),
            (EntityType.EVENT, EntityType.PERSON)
        ]
        
        if (type1, type2) in high_value_pairs or (type2, type1) in high_value_pairs:
            return 0.2
        
        return 0.0
    
    def _find_matching_entity(self, text: str, entity_texts: List[str]) -> Optional[str]:
        """Find entity that matches the given text"""
        text_lower = text.lower().strip()
        
        # Exact match
        for entity_text in entity_texts:
            if entity_text.lower() == text_lower:
                return entity_text
        
        # Partial match
        for entity_text in entity_texts:
            if entity_text.lower() in text_lower or text_lower in entity_text.lower():
                return entity_text
        
        return None
    
    async def _extract_with_llm(self, text: str, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract relationships using LLM assistance"""
        relationships = []
        
        try:
            entity_list = [e["text"] for e in entities]
            prompt = f"""
            Given the following entities from a text, identify relationships between them:
            
            Entities: {', '.join(entity_list)}
            
            Text: {text[:800]}
            
            Return relationships in JSON format with: source, target, relationship_type, confidence (0-1)
            Relationship types: related_to, part_of, causes, similar_to, opposite_of, defined_by, example_of
            """
            
            response = await self._query_llm(prompt)
            if response:
                llm_relationships = self._parse_llm_relationships(response, entity_list)
                relationships.extend(llm_relationships)
                
        except Exception as e:
            logger.warning(f"LLM relationship extraction failed: {str(e)}")
        
        return relationships
    
    async def _query_llm(self, prompt: str) -> Optional[str]:
        """Query local LLM for relationship extraction"""
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama2",
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get("response", "")
        except Exception as e:
            logger.warning(f"LLM query failed: {str(e)}")
        
        return None
    
    def _parse_llm_relationships(self, response: str, entity_list: List[str]) -> List[Dict[str, Any]]:
        """Parse LLM response to extract relationships"""
        relationships = []
        
        try:
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                relationship_data = json.loads(json_match.group())
                
                for item in relationship_data:
                    if isinstance(item, dict) and all(k in item for k in ["source", "target"]):
                        source = item["source"]
                        target = item["target"]
                        
                        # Validate entities exist
                        if source in entity_list and target in entity_list and source != target:
                            rel_type = self._map_llm_relationship_type(
                                item.get("relationship_type", "related_to")
                            )
                            
                            relationships.append({
                                "source": source,
                                "target": target,
                                "type": rel_type,
                                "confidence": float(item.get("confidence", 0.7)),
                                "context": "",
                                "source_method": "llm",
                                "metadata": {"llm_type": item.get("relationship_type")}
                            })
        except Exception as e:
            logger.warning(f"Failed to parse LLM relationships: {str(e)}")
        
        return relationships
    
    def _map_llm_relationship_type(self, llm_type: str) -> RelationshipType:
        """Map LLM relationship type to our schema"""
        type_mapping = {
            "related_to": RelationshipType.RELATED_TO,
            "part_of": RelationshipType.PART_OF,
            "causes": RelationshipType.CAUSES,
            "similar_to": RelationshipType.SIMILAR_TO,
            "opposite_of": RelationshipType.OPPOSITE_OF,
            "defined_by": RelationshipType.DEFINED_BY,
            "example_of": RelationshipType.EXAMPLE_OF
        }
        return type_mapping.get(llm_type.lower(), RelationshipType.RELATED_TO)
    
    async def _score_and_filter_relationships(
        self, 
        relationships: List[Dict[str, Any]], 
        text: str
    ) -> List[Dict[str, Any]]:
        """Score and filter relationships"""
        # Remove duplicates
        unique_relationships = {}
        for rel in relationships:
            key = (rel["source"], rel["target"], rel["type"])
            if key not in unique_relationships or rel["confidence"] > unique_relationships[key]["confidence"]:
                unique_relationships[key] = rel
        
        # Filter by minimum confidence
        filtered_relationships = [
            rel for rel in unique_relationships.values() 
            if rel["confidence"] >= 0.3
        ]
        
        # Sort by confidence
        return sorted(filtered_relationships, key=lambda x: x["confidence"], reverse=True)


class GraphBuilder:
    """Constructs and maintains knowledge graphs"""
    
    def __init__(self):
        self.graph = nx.DiGraph()
    
    async def build_graph_from_entities_and_relationships(
        self, 
        entities: List[Dict[str, Any]], 
        relationships: List[Dict[str, Any]]
    ) -> nx.DiGraph:
        """Build a NetworkX graph from entities and relationships"""
        # Clear existing graph
        self.graph.clear()
        
        # Add entities as nodes
        for entity in entities:
            entity_id = f"{entity.get('type', 'ENTITY')}:{entity['name']}"
            self.graph.add_node(entity_id, **{
                "name": entity["name"],
                "type": entity.get("type", "ENTITY"),
                "importance": entity.get("importance_score", 0.0),
                "metadata": entity.get("metadata", {})
            })
        
        # Add relationships as edges
        for rel in relationships:
            # Find matching nodes by entity name
            source_id = None
            target_id = None
            
            for node_id, node_data in self.graph.nodes(data=True):
                if node_data["name"] == rel["source_entity_name"]:
                    source_id = node_id
                elif node_data["name"] == rel["target_entity_name"]:
                    target_id = node_id
            
            if source_id and target_id:
                self.graph.add_edge(source_id, target_id, **{
                    "relationship_type": rel["relationship_type"],
                    "confidence": rel["confidence_score"],
                    "context": rel.get("context", ""),
                    "metadata": rel.get("metadata", {})
                })
        
        return self.graph
    
    async def update_graph_with_new_document(
        self, 
        document_id: str, 
        entities: List[Dict[str, Any]], 
        relationships: List[Dict[str, Any]]
    ) -> None:
        """Update existing graph with new document data"""
        # Add new entities
        for entity in entities:
            entity_id = f"{entity.get('type', 'ENTITY')}:{entity['name']}"
            
            if self.graph.has_node(entity_id):
                # Update existing node
                node_data = self.graph.nodes[entity_id]
                node_data["importance"] = max(
                    node_data.get("importance", 0.0),
                    entity.get("importance_score", 0.0)
                )
                # Add document to sources
                if "documents" not in node_data:
                    node_data["documents"] = set()
                node_data["documents"].add(document_id)
            else:
                # Add new node
                self.graph.add_node(entity_id, **{
                    "name": entity["name"],
                    "type": entity.get("type", "ENTITY"),
                    "importance": entity.get("importance_score", 0.0),
                    "documents": {document_id},
                    "metadata": entity.get("metadata", {})
                })
        
        # Add new relationships
        for rel in relationships:
            # Find matching nodes by entity name
            source_id = None
            target_id = None
            
            for node_id, node_data in self.graph.nodes(data=True):
                if node_data["name"] == rel["source_entity_name"]:
                    source_id = node_id
                elif node_data["name"] == rel["target_entity_name"]:
                    target_id = node_id
            
            if source_id and target_id:
                if self.graph.has_edge(source_id, target_id):
                    # Update existing edge
                    edge_data = self.graph.edges[source_id, target_id]
                    edge_data["confidence"] = max(
                        edge_data.get("confidence", 0.0),
                        rel["confidence_score"]
                    )
                    # Add document to sources
                    if "documents" not in edge_data:
                        edge_data["documents"] = set()
                    edge_data["documents"].add(document_id)
                else:
                    # Add new edge
                    self.graph.add_edge(source_id, target_id, **{
                        "relationship_type": rel["relationship_type"],
                        "confidence": rel["confidence_score"],
                        "context": rel.get("context", ""),
                        "documents": {document_id},
                        "metadata": rel.get("metadata", {})
                    })
    
    async def get_subgraph(self, entity_names: List[str], max_depth: int = 2) -> nx.DiGraph:
        """Extract a subgraph around specific entities"""
        if not entity_names:
            return nx.DiGraph()
        
        # Find all matching nodes
        seed_nodes = []
        for entity_name in entity_names:
            for node_id in self.graph.nodes():
                if entity_name.lower() in self.graph.nodes[node_id]["name"].lower():
                    seed_nodes.append(node_id)
        
        if not seed_nodes:
            return nx.DiGraph()
        
        # Get nodes within max_depth
        subgraph_nodes = set(seed_nodes)
        current_nodes = set(seed_nodes)
        
        for depth in range(max_depth):
            next_nodes = set()
            for node in current_nodes:
                # Add neighbors
                neighbors = set(self.graph.predecessors(node)) | set(self.graph.successors(node))
                next_nodes.update(neighbors)
            
            subgraph_nodes.update(next_nodes)
            current_nodes = next_nodes
            
            if not next_nodes:
                break
        
        return self.graph.subgraph(subgraph_nodes).copy()
    
    async def calculate_centrality_metrics(self) -> Dict[str, Dict[str, float]]:
        """Calculate various centrality metrics for nodes"""
        if not self.graph.nodes():
            return {}
        
        try:
            metrics = {}
            
            # Degree centrality
            degree_centrality = nx.degree_centrality(self.graph)
            
            # Betweenness centrality
            betweenness_centrality = nx.betweenness_centrality(self.graph)
            
            # PageRank
            pagerank = nx.pagerank(self.graph)
            
            # Combine metrics
            for node in self.graph.nodes():
                metrics[node] = {
                    "degree_centrality": degree_centrality.get(node, 0.0),
                    "betweenness_centrality": betweenness_centrality.get(node, 0.0),
                    "pagerank": pagerank.get(node, 0.0)
                }
            
            return metrics
        except Exception as e:
            logger.error(f"Error calculating centrality metrics: {str(e)}")
            return {}


class GraphQueryEngine:
    """Enables semantic queries over the knowledge graph"""
    
    def __init__(self, graph_builder: GraphBuilder):
        self.graph_builder = graph_builder
        self.graph = graph_builder.graph
    
    async def find_shortest_path(self, source_entity: str, target_entity: str) -> List[Dict[str, Any]]:
        """Find shortest path between two entities"""
        # Find matching nodes
        source_nodes = self._find_matching_nodes(source_entity)
        target_nodes = self._find_matching_nodes(target_entity)
        
        if not source_nodes or not target_nodes:
            return []
        
        shortest_paths = []
        
        for source_node in source_nodes:
            for target_node in target_nodes:
                try:
                    path = nx.shortest_path(self.graph, source_node, target_node)
                    path_info = []
                    
                    for i in range(len(path) - 1):
                        current_node = path[i]
                        next_node = path[i + 1]
                        edge_data = self.graph.edges[current_node, next_node]
                        
                        path_info.append({
                            "from": self.graph.nodes[current_node]["name"],
                            "to": self.graph.nodes[next_node]["name"],
                            "relationship": edge_data["relationship_type"],
                            "confidence": edge_data["confidence"]
                        })
                    
                    shortest_paths.append({
                        "path_length": len(path) - 1,
                        "path": path_info,
                        "total_confidence": sum(step["confidence"] for step in path_info) / len(path_info) if path_info else 0.0
                    })
                    
                except nx.NetworkXNoPath:
                    continue
        
        # Sort by path length and confidence
        return sorted(shortest_paths, key=lambda x: (x["path_length"], -x["total_confidence"]))
    
    async def find_entities_by_type(self, entity_type: str, min_importance: float = 0.0) -> List[Dict[str, Any]]:
        """Find all entities of a specific type"""
        matching_entities = []
        
        for node_id, node_data in self.graph.nodes(data=True):
            if (node_data.get("type", "").lower() == entity_type.lower() and 
                node_data.get("importance", 0.0) >= min_importance):
                
                matching_entities.append({
                    "id": node_id,
                    "name": node_data["name"],
                    "type": node_data["type"],
                    "importance": node_data.get("importance", 0.0),
                    "metadata": node_data.get("metadata", {})
                })
        
        return sorted(matching_entities, key=lambda x: x["importance"], reverse=True)
    
    async def find_related_entities(
        self, 
        entity_name: str, 
        relationship_types: List[str] = None, 
        max_depth: int = 2,
        min_confidence: float = 0.0
    ) -> List[Dict[str, Any]]:
        """Find entities related to a given entity"""
        matching_nodes = self._find_matching_nodes(entity_name)
        if not matching_nodes:
            return []
        
        related_entities = []
        
        for source_node in matching_nodes:
            # BFS to find related entities
            visited = set()
            queue = [(source_node, 0, 1.0)]  # (node, depth, confidence)
            
            while queue:
                current_node, depth, path_confidence = queue.pop(0)
                
                if current_node in visited or depth >= max_depth:
                    continue
                
                visited.add(current_node)
                
                # Check outgoing edges
                for neighbor in self.graph.successors(current_node):
                    edge_data = self.graph.edges[current_node, neighbor]
                    edge_confidence = edge_data.get("confidence", 0.0)
                    
                    if edge_confidence < min_confidence:
                        continue
                    
                    if relationship_types and edge_data.get("relationship_type") not in relationship_types:
                        continue
                    
                    neighbor_data = self.graph.nodes[neighbor]
                    combined_confidence = path_confidence * edge_confidence
                    
                    related_entities.append({
                        "entity": neighbor_data["name"],
                        "type": neighbor_data.get("type", "ENTITY"),
                        "relationship": edge_data["relationship_type"],
                        "confidence": combined_confidence,
                        "depth": depth + 1,
                        "context": edge_data.get("context", ""),
                        "path_from_source": f"{self.graph.nodes[source_node]['name']} -> {neighbor_data['name']}"
                    })
                    
                    queue.append((neighbor, depth + 1, combined_confidence))
                
                # Check incoming edges
                for predecessor in self.graph.predecessors(current_node):
                    edge_data = self.graph.edges[predecessor, current_node]
                    edge_confidence = edge_data.get("confidence", 0.0)
                    
                    if edge_confidence < min_confidence:
                        continue
                    
                    if relationship_types and edge_data.get("relationship_type") not in relationship_types:
                        continue
                    
                    predecessor_data = self.graph.nodes[predecessor]
                    combined_confidence = path_confidence * edge_confidence
                    
                    related_entities.append({
                        "entity": predecessor_data["name"],
                        "type": predecessor_data.get("type", "ENTITY"),
                        "relationship": edge_data["relationship_type"],
                        "confidence": combined_confidence,
                        "depth": depth + 1,
                        "context": edge_data.get("context", ""),
                        "path_from_source": f"{predecessor_data['name']} -> {self.graph.nodes[source_node]['name']}"
                    })
                    
                    queue.append((predecessor, depth + 1, combined_confidence))
        
        # Remove duplicates and sort by confidence
        unique_entities = {}
        for entity in related_entities:
            key = entity["entity"]
            if key not in unique_entities or entity["confidence"] > unique_entities[key]["confidence"]:
                unique_entities[key] = entity
        
        return sorted(unique_entities.values(), key=lambda x: x["confidence"], reverse=True)
    
    async def query_by_pattern(self, pattern: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Query graph using pattern matching"""
        results = []
        
        # Extract pattern components
        source_type = pattern.get("source_type")
        target_type = pattern.get("target_type")
        relationship_type = pattern.get("relationship_type")
        min_confidence = pattern.get("min_confidence", 0.0)
        
        # Find matching patterns
        for source_node, target_node, edge_data in self.graph.edges(data=True):
            source_data = self.graph.nodes[source_node]
            target_data = self.graph.nodes[target_node]
            
            # Check if pattern matches
            if source_type and source_data.get("type", "").lower() != source_type.lower():
                continue
            
            if target_type and target_data.get("type", "").lower() != target_type.lower():
                continue
            
            if relationship_type and edge_data.get("relationship_type", "").lower() != relationship_type.lower():
                continue
            
            if edge_data.get("confidence", 0.0) < min_confidence:
                continue
            
            results.append({
                "source": {
                    "name": source_data["name"],
                    "type": source_data.get("type", "ENTITY"),
                    "importance": source_data.get("importance", 0.0)
                },
                "target": {
                    "name": target_data["name"],
                    "type": target_data.get("type", "ENTITY"),
                    "importance": target_data.get("importance", 0.0)
                },
                "relationship": edge_data["relationship_type"],
                "confidence": edge_data["confidence"],
                "context": edge_data.get("context", "")
            })
        
        return sorted(results, key=lambda x: x["confidence"], reverse=True)
    
    async def get_graph_statistics(self) -> Dict[str, Any]:
        """Get comprehensive graph statistics"""
        if not self.graph.nodes():
            return {
                "total_nodes": 0,
                "total_edges": 0,
                "density": 0.0,
                "connected_components": 0,
                "average_clustering": 0.0
            }
        
        try:
            # Basic statistics
            total_nodes = self.graph.number_of_nodes()
            total_edges = self.graph.number_of_edges()
            density = nx.density(self.graph)
            
            # Convert to undirected for some metrics
            undirected_graph = self.graph.to_undirected()
            connected_components = nx.number_connected_components(undirected_graph)
            average_clustering = nx.average_clustering(undirected_graph)
            
            # Node type distribution
            node_types = {}
            for node_data in self.graph.nodes(data=True):
                node_type = node_data[1].get("type", "UNKNOWN")
                node_types[node_type] = node_types.get(node_type, 0) + 1
            
            # Relationship type distribution
            relationship_types = {}
            for edge_data in self.graph.edges(data=True):
                rel_type = edge_data[2].get("relationship_type", "UNKNOWN")
                relationship_types[rel_type] = relationship_types.get(rel_type, 0) + 1
            
            return {
                "total_nodes": total_nodes,
                "total_edges": total_edges,
                "density": density,
                "connected_components": connected_components,
                "average_clustering": average_clustering,
                "node_types": node_types,
                "relationship_types": relationship_types,
                "average_degree": sum(dict(self.graph.degree()).values()) / total_nodes if total_nodes > 0 else 0.0
            }
            
        except Exception as e:
            logger.error(f"Error calculating graph statistics: {str(e)}")
            return {"error": str(e)}
    
    def _find_matching_nodes(self, entity_name: str) -> List[str]:
        """Find nodes that match the given entity name"""
        matching_nodes = []
        entity_name_lower = entity_name.lower()
        
        for node_id, node_data in self.graph.nodes(data=True):
            node_name_lower = node_data["name"].lower()
            
            # Exact match
            if node_name_lower == entity_name_lower:
                matching_nodes.append(node_id)
            # Partial match
            elif entity_name_lower in node_name_lower or node_name_lower in entity_name_lower:
                matching_nodes.append(node_id)
        
        return matching_nodes


class EnhancedKnowledgeGraphService:
    """Enhanced Knowledge Graph Service with entity extraction and relationship mapping"""
    
    def __init__(self):
        self.graph_builder = GraphBuilder()
        self.query_engine = GraphQueryEngine(self.graph_builder)
        self.entity_extractor = EntityExtractor()
        self.relationship_mapper = RelationshipMapper()
        # Provide direct access to graph for backward compatibility
        self.graph = self.graph_builder.graph
    
    async def initialize(self):
        """Initialize knowledge graph service"""
        logger.info("Enhanced Knowledge graph service initialized")
    
    async def add_document(self, document_data: Dict[str, Any]):
        """Add document to enhanced knowledge graph with entity extraction and relationship mapping"""
        try:
            db = next(get_db())
            
            # Get document chunks
            chunks = db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_data["id"]
            ).all()
            
            all_entities = []
            all_relationships = []
            
            # Extract entities and relationships from each chunk
            for chunk in chunks:
                # Use enhanced entity extraction
                entities = await self.entity_extractor.extract_entities(chunk.content)
                relationships = await self.relationship_mapper.extract_relationships(
                    chunk.content, entities
                )
                
                # Store entities in database
                for entity_data in entities:
                    entity = await self._store_entity_in_db(
                        entity_data, document_data["id"], chunk.id, db
                    )
                    if entity:
                        all_entities.append(entity)
                
                # Store relationships in database
                for rel_data in relationships:
                    relationship = await self._store_relationship_in_db(
                        rel_data, document_data["id"], all_entities, db
                    )
                    if relationship:
                        all_relationships.append(relationship)
            
            # Update the in-memory graph using GraphBuilder
            await self._update_graph_with_document_data(document_data["id"], all_entities, all_relationships)
            
            logger.info(f"Added document {document_data['id']} to enhanced knowledge graph with {len(all_entities)} entities and {len(all_relationships)} relationships")
            
        except Exception as e:
            logger.error(f"Error adding document to knowledge graph: {str(e)}")
        finally:
            if 'db' in locals():
                db.close()
    
    async def _update_graph_with_document_data(
        self, 
        document_id: str, 
        entities: List[Dict[str, Any]], 
        relationships: List[Dict[str, Any]]
    ):
        """Update the in-memory graph with document data"""
        # Convert entity data to format expected by GraphBuilder
        entity_data = []
        for entity in entities:
            entity_data.append({
                "name": entity["name"],
                "type": entity["type"],
                "importance_score": entity["importance_score"],
                "metadata": entity.get("metadata", {})
            })
        
        # Convert relationship data to format expected by GraphBuilder
        relationship_data = []
        for rel in relationships:
            relationship_data.append({
                "source_entity_name": rel["source_entity_name"],
                "target_entity_name": rel["target_entity_name"],
                "relationship_type": rel["relationship_type"],
                "confidence_score": rel["confidence_score"],
                "context": rel.get("context", ""),
                "metadata": rel.get("metadata", {})
            })
        
        # Update the graph
        await self.graph_builder.update_graph_with_new_document(
            document_id, entity_data, relationship_data
        )
    
    async def _store_entity_in_db(
        self, 
        entity_data: Dict[str, Any], 
        document_id: str, 
        chunk_id: str, 
        db
    ) -> Optional[KnowledgeGraphEntity]:
        """Store entity in database"""
        try:
            # Check if entity already exists
            existing_entity = db.query(KnowledgeGraphEntity).filter(
                KnowledgeGraphEntity.name == entity_data["text"],
                KnowledgeGraphEntity.type == entity_data["type"].value
            ).first()
            
            if existing_entity:
                # Update importance score
                existing_entity.importance_score = min(
                    1.0, 
                    existing_entity.importance_score + entity_data["confidence"] * 0.1
                )
                db.commit()
                return existing_entity
            else:
                # Create new entity
                entity = KnowledgeGraphEntity(
                    name=entity_data["text"],
                    type=entity_data["type"].value,
                    description=f"Entity extracted from document {document_id}",
                    importance_score=entity_data["confidence"],
                    document_id=document_id,
                    metadata={
                        "extraction_source": entity_data["source"],
                        "chunk_id": chunk_id,
                        "confidence": entity_data["confidence"],
                        **entity_data.get("metadata", {})
                    }
                )
                
                db.add(entity)
                db.commit()
                db.refresh(entity)
                return entity
                
        except Exception as e:
            logger.error(f"Error storing entity in database: {str(e)}")
            db.rollback()
            return None
    
    async def _store_relationship_in_db(
        self, 
        rel_data: Dict[str, Any], 
        document_id: str, 
        entities: List[KnowledgeGraphEntity], 
        db
    ) -> Optional[KnowledgeGraphRelationship]:
        """Store relationship in database"""
        try:
            # Find source and target entities
            source_entity = None
            target_entity = None
            
            for entity in entities:
                if entity.name == rel_data["source"]:
                    source_entity = entity
                elif entity.name == rel_data["target"]:
                    target_entity = entity
            
            if not source_entity or not target_entity:
                return None
            
            # Check if relationship already exists
            existing_rel = db.query(KnowledgeGraphRelationship).filter(
                KnowledgeGraphRelationship.source_entity_id == source_entity.id,
                KnowledgeGraphRelationship.target_entity_id == target_entity.id,
                KnowledgeGraphRelationship.relationship_type == rel_data["type"].value
            ).first()
            
            if existing_rel:
                # Update confidence score
                existing_rel.confidence_score = max(
                    existing_rel.confidence_score,
                    rel_data["confidence"]
                )
                db.commit()
                return existing_rel
            else:
                # Create new relationship
                relationship = KnowledgeGraphRelationship(
                    source_entity_id=source_entity.id,
                    target_entity_id=target_entity.id,
                    relationship_type=rel_data["type"].value,
                    confidence_score=rel_data["confidence"],
                    context=rel_data.get("context", ""),
                    metadata={
                        "extraction_method": rel_data.get("source_method", "unknown"),
                        "document_id": document_id,
                        **rel_data.get("metadata", {})
                    }
                )
                
                db.add(relationship)
                db.commit()
                db.refresh(relationship)
                return relationship
                
        except Exception as e:
            logger.error(f"Error storing relationship in database: {str(e)}")
            db.rollback()
            return None

    async def query_graph(self, query: str, user_id: str = None) -> Dict[str, Any]:
        """Query the knowledge graph using semantic search"""
        try:
            # Parse query to extract entities and relationships
            query_lower = query.lower()
            
            # Simple keyword extraction for entities
            entities_in_query = []
            for node_id, node_data in self.graph_builder.graph.nodes(data=True):
                entity_name = node_data["name"].lower()
                if entity_name in query_lower or any(word in entity_name for word in query_lower.split()):
                    entities_in_query.append(node_data["name"])
            
            if not entities_in_query:
                return {"results": [], "message": "No matching entities found in the knowledge graph"}
            
            # Find related entities for each found entity
            all_results = []
            for entity_name in entities_in_query[:3]:  # Limit to top 3 matches
                related = await self.query_engine.find_related_entities(
                    entity_name, max_depth=2, min_confidence=0.3
                )
                all_results.extend(related)
            
            # Remove duplicates and sort by confidence
            unique_results = {}
            for result in all_results:
                key = result["entity"]
                if key not in unique_results or result["confidence"] > unique_results[key]["confidence"]:
                    unique_results[key] = result
            
            final_results = sorted(unique_results.values(), key=lambda x: x["confidence"], reverse=True)
            
            return {
                "query": query,
                "entities_found": entities_in_query,
                "results": final_results[:10],  # Top 10 results
                "total_results": len(final_results)
            }
            
        except Exception as e:
            logger.error(f"Error querying knowledge graph: {str(e)}")
            return {"error": str(e), "results": []}
    
    async def get_entity_connections(self, entity_id: str, depth: int = 2) -> List[Dict[str, Any]]:
        """Get connections for a specific entity"""
        try:
            db = next(get_db())
            
            # Get entity from database
            entity = db.query(KnowledgeGraphEntity).filter(
                KnowledgeGraphEntity.id == entity_id
            ).first()
            
            if not entity:
                return []
            
            # Use query engine to find related entities
            related = await self.query_engine.find_related_entities(
                entity.name, max_depth=depth, min_confidence=0.2
            )
            
            return related
            
        except Exception as e:
            logger.error(f"Error getting entity connections: {str(e)}")
            return []
        finally:
            if 'db' in locals():
                db.close()
    
    async def build_full_graph_from_database(self) -> None:
        """Build the complete in-memory graph from database"""
        try:
            db = next(get_db())
            
            # Get all entities
            entities = db.query(KnowledgeGraphEntity).all()
            
            # Get all relationships
            relationships = db.query(KnowledgeGraphRelationship).all()
            
            # Convert to format expected by GraphBuilder
            entity_data = []
            for entity in entities:
                entity_data.append({
                    "name": entity.name,
                    "type": entity.type,
                    "importance_score": entity.importance_score,
                    "metadata": entity.entity_metadata or {}
                })
            
            relationship_data = []
            entity_lookup = {e.id: e for e in entities}
            
            for rel in relationships:
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
            
            # Build the graph
            await self.graph_builder.build_graph_from_entities_and_relationships(
                entity_data, relationship_data
            )
            
            logger.info(f"Built complete knowledge graph with {len(entity_data)} entities and {len(relationship_data)} relationships")
            
        except Exception as e:
            logger.error(f"Error building graph from database: {str(e)}")
        finally:
            if 'db' in locals():
                db.close()

    async def get_document_graph(self, document_id: str) -> Dict[str, Any]:
        """Get enhanced knowledge graph for a specific document"""
        try:
            db = next(get_db())
            
            # Get entities from database
            entities = db.query(KnowledgeGraphEntity).filter(
                KnowledgeGraphEntity.document_id == document_id
            ).all()
            
            # Get relationships from database
            entity_ids = [e.id for e in entities]
            relationships = db.query(KnowledgeGraphRelationship).filter(
                KnowledgeGraphRelationship.source_entity_id.in_(entity_ids)
            ).all()
            
            # Format response
            nodes = []
            for entity in entities:
                nodes.append({
                    "id": entity.id,
                    "label": entity.name,
                    "type": entity.type,
                    "importance": entity.importance_score,
                    "metadata": entity.entity_metadata
                })
            
            edges = []
            for rel in relationships:
                edges.append({
                    "source": rel.source_entity_id,
                    "target": rel.target_entity_id,
                    "relationship": rel.relationship_type,
                    "weight": rel.confidence_score,
                    "context": rel.context
                })
            
            return {
                "nodes": nodes,
                "edges": edges,
                "metadata": {
                    "total_nodes": len(nodes),
                    "total_edges": len(edges),
                    "document_id": document_id
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting document graph: {str(e)}")
            return {"nodes": [], "edges": [], "metadata": {}}
        finally:
            if 'db' in locals():
                db.close()

    async def get_graph_statistics(self) -> Dict[str, Any]:
        """Get enhanced knowledge graph statistics"""
        try:
            db = next(get_db())
            
            from sqlalchemy import func
            
            # Get entity statistics
            total_entities = db.query(KnowledgeGraphEntity).count()
            entity_types = db.query(
                KnowledgeGraphEntity.type,
                func.count(KnowledgeGraphEntity.id)
            ).group_by(KnowledgeGraphEntity.type).all()
            
            # Get relationship statistics
            total_relationships = db.query(KnowledgeGraphRelationship).count()
            relationship_types = db.query(
                KnowledgeGraphRelationship.relationship_type,
                func.count(KnowledgeGraphRelationship.id)
            ).group_by(KnowledgeGraphRelationship.relationship_type).all()
            
            # Calculate average confidence scores
            avg_entity_confidence = db.query(
                func.avg(KnowledgeGraphEntity.importance_score)
            ).scalar() or 0.0
            
            avg_relationship_confidence = db.query(
                func.avg(KnowledgeGraphRelationship.confidence_score)
            ).scalar() or 0.0
            
            return {
                "total_entities": total_entities,
                "total_relationships": total_relationships,
                "entity_types": dict(entity_types),
                "relationship_types": dict(relationship_types),
                "average_entity_confidence": float(avg_entity_confidence),
                "average_relationship_confidence": float(avg_relationship_confidence),
                "graph_density": total_relationships / max(1, total_entities * (total_entities - 1)) if total_entities > 1 else 0.0
            }
            
        except Exception as e:
            logger.error(f"Error getting graph statistics: {str(e)}")
            return {}
        finally:
            if 'db' in locals():
                db.close()

    async def find_related_entities(self, entity_name: str, max_depth: int = 2) -> List[Dict[str, Any]]:
        """Find entities related to a given entity"""
        try:
            db = next(get_db())
            
            # Find the source entity
            source_entity = db.query(KnowledgeGraphEntity).filter(
                KnowledgeGraphEntity.name.ilike(f"%{entity_name}%")
            ).first()
            
            if not source_entity:
                return []
            
            from sqlalchemy import or_
            
            # Find direct relationships
            relationships = db.query(KnowledgeGraphRelationship).filter(
                or_(
                    KnowledgeGraphRelationship.source_entity_id == source_entity.id,
                    KnowledgeGraphRelationship.target_entity_id == source_entity.id
                )
            ).all()
            
            related_entities = []
            for rel in relationships:
                # Get the other entity in the relationship
                other_entity_id = (
                    rel.target_entity_id if rel.source_entity_id == source_entity.id 
                    else rel.source_entity_id
                )
                
                other_entity = db.query(KnowledgeGraphEntity).filter(
                    KnowledgeGraphEntity.id == other_entity_id
                ).first()
                
                if other_entity:
                    related_entities.append({
                        "entity": other_entity.name,
                        "type": other_entity.type,
                        "relationship": rel.relationship_type,
                        "confidence": rel.confidence_score,
                        "context": rel.context,
                        "depth": 1
                    })
            
            return sorted(related_entities, key=lambda x: x["confidence"], reverse=True)
            
        except Exception as e:
            logger.error(f"Error finding related entities: {str(e)}")
            return []
        finally:
            if 'db' in locals():
                db.close()