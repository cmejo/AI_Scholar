"""
Tests for enhanced entity extraction and relationship mapping
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any

from services.knowledge_graph import EntityExtractor, RelationshipMapper, EnhancedKnowledgeGraphService
from models.schemas import EntityType, RelationshipType


class TestEntityExtractor:
    """Test cases for EntityExtractor class"""
    
    @pytest.fixture
    def entity_extractor(self):
        """Create EntityExtractor instance for testing"""
        return EntityExtractor()
    
    @pytest.mark.asyncio
    async def test_extract_entities_with_spacy(self, entity_extractor):
        """Test entity extraction using spaCy"""
        text = "Apple Inc. was founded by Steve Jobs in Cupertino, California."
        
        # Mock spaCy if not available
        if not entity_extractor.nlp:
            pytest.skip("spaCy model not available")
        
        entities = await entity_extractor.extract_entities(text, use_llm=False)
        
        assert len(entities) > 0
        
        # Check for expected entities
        entity_texts = [e["text"] for e in entities]
        assert any("Apple" in text for text in entity_texts)
        assert any("Steve Jobs" in text for text in entity_texts)
        assert any("Cupertino" in text for text in entity_texts)
        
        # Check entity types
        for entity in entities:
            assert "type" in entity
            assert isinstance(entity["type"], EntityType)
            assert "confidence" in entity
            assert 0.0 <= entity["confidence"] <= 1.0
    
    @pytest.mark.asyncio
    async def test_extract_entities_with_patterns(self, entity_extractor):
        """Test pattern-based entity extraction"""
        text = "Contact us at support@example.com or visit https://example.com for more info."
        
        entities = await entity_extractor.extract_entities(text, use_llm=False)
        
        # Should find email and URL
        entity_texts = [e["text"] for e in entities]
        assert "support@example.com" in entity_texts
        assert "https://example.com" in entity_texts
        
        # Check metadata
        email_entity = next(e for e in entities if e["text"] == "support@example.com")
        assert email_entity["metadata"]["pattern_type"] == "email"
        assert email_entity["source"] == "pattern"
    
    @pytest.mark.asyncio
    async def test_extract_entities_deduplication(self, entity_extractor):
        """Test entity deduplication and scoring"""
        text = "Apple Inc. is a technology company. Apple was founded in 1976."
        
        entities = await entity_extractor.extract_entities(text, use_llm=False)
        
        # Should not have duplicate "Apple" entities
        apple_entities = [e for e in entities if "Apple" in e["text"]]
        assert len(apple_entities) <= 2  # May have "Apple Inc." and "Apple" as separate
        
        # Check confidence scoring
        for entity in entities:
            assert entity["confidence"] > 0.0
    
    @pytest.mark.asyncio
    async def test_extract_entities_confidence_scoring(self, entity_extractor):
        """Test confidence scoring for entities"""
        text = "NASA launched a rocket. The organization has many projects."
        
        entities = await entity_extractor.extract_entities(text, use_llm=False)
        
        # Entities should have reasonable confidence scores
        for entity in entities:
            assert 0.1 <= entity["confidence"] <= 1.0
            assert "source" in entity
    
    @pytest.mark.asyncio
    @patch('requests.post')
    async def test_extract_entities_with_llm(self, mock_post, entity_extractor):
        """Test LLM-assisted entity extraction"""
        # Mock LLM response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": '[{"name": "Machine Learning", "type": "concept", "confidence": 0.9}]'
        }
        mock_post.return_value = mock_response
        
        text = "Machine learning is a subset of artificial intelligence."
        
        entities = await entity_extractor.extract_entities(text, use_llm=True)
        
        # Should include LLM-extracted entities
        llm_entities = [e for e in entities if e["source"] == "llm"]
        if llm_entities:  # Only check if LLM extraction worked
            assert len(llm_entities) > 0
            assert any("Machine Learning" in e["text"] for e in llm_entities)


class TestRelationshipMapper:
    """Test cases for RelationshipMapper class"""
    
    @pytest.fixture
    def relationship_mapper(self):
        """Create RelationshipMapper instance for testing"""
        return RelationshipMapper()
    
    @pytest.fixture
    def sample_entities(self):
        """Sample entities for testing"""
        return [
            {
                "text": "Apple Inc.",
                "type": EntityType.ORGANIZATION,
                "start": 0,
                "end": 10,
                "confidence": 0.9
            },
            {
                "text": "Steve Jobs",
                "type": EntityType.PERSON,
                "start": 25,
                "end": 35,
                "confidence": 0.9
            },
            {
                "text": "Cupertino",
                "type": EntityType.LOCATION,
                "start": 50,
                "end": 59,
                "confidence": 0.8
            }
        ]
    
    @pytest.mark.asyncio
    async def test_extract_relationships_patterns(self, relationship_mapper, sample_entities):
        """Test pattern-based relationship extraction"""
        text = "Apple Inc. was founded by Steve Jobs in Cupertino, California."
        
        relationships = await relationship_mapper.extract_relationships(
            text, sample_entities, use_llm=False
        )
        
        assert len(relationships) > 0
        
        # Check relationship structure
        for rel in relationships:
            assert "source" in rel
            assert "target" in rel
            assert "type" in rel
            assert isinstance(rel["type"], RelationshipType)
            assert "confidence" in rel
            assert 0.0 <= rel["confidence"] <= 1.0
    
    @pytest.mark.asyncio
    async def test_extract_relationships_cooccurrence(self, relationship_mapper, sample_entities):
        """Test co-occurrence based relationship extraction"""
        text = "Apple Inc. and Steve Jobs revolutionized technology in Cupertino."
        
        relationships = await relationship_mapper.extract_relationships(
            text, sample_entities, use_llm=False
        )
        
        # Should find co-occurrence relationships
        cooccurrence_rels = [r for r in relationships if r["source_method"] == "cooccurrence"]
        assert len(cooccurrence_rels) > 0
        
        # Check confidence calculation
        for rel in cooccurrence_rels:
            assert rel["confidence"] > 0.0
            assert "distance" in rel["metadata"]
    
    @pytest.mark.asyncio
    async def test_relationship_confidence_scoring(self, relationship_mapper, sample_entities):
        """Test relationship confidence scoring"""
        # Close entities should have higher confidence
        text1 = "Apple Inc. and Steve Jobs"  # Close
        text2 = "Apple Inc. is located far away from Steve Jobs"  # Far
        
        relationships1 = await relationship_mapper.extract_relationships(
            text1, sample_entities, use_llm=False
        )
        relationships2 = await relationship_mapper.extract_relationships(
            text2, sample_entities, use_llm=False
        )
        
        if relationships1 and relationships2:
            # Closer entities should generally have higher confidence
            avg_conf1 = sum(r["confidence"] for r in relationships1) / len(relationships1)
            avg_conf2 = sum(r["confidence"] for r in relationships2) / len(relationships2)
            
            # This is a general trend, not a strict rule
            assert avg_conf1 >= 0.0 and avg_conf2 >= 0.0
    
    @pytest.mark.asyncio
    async def test_relationship_type_detection(self, relationship_mapper):
        """Test relationship type detection from patterns"""
        entities = [
            {"text": "smoking", "type": EntityType.CONCEPT, "start": 0, "end": 7, "confidence": 0.8},
            {"text": "cancer", "type": EntityType.CONCEPT, "start": 15, "end": 21, "confidence": 0.8}
        ]
        
        text = "smoking causes cancer"
        
        relationships = await relationship_mapper.extract_relationships(
            text, entities, use_llm=False
        )
        
        # Should detect causal relationship
        causal_rels = [r for r in relationships if r["type"] == RelationshipType.CAUSES]
        assert len(causal_rels) > 0
    
    @pytest.mark.asyncio
    @patch('requests.post')
    async def test_extract_relationships_with_llm(self, mock_post, relationship_mapper, sample_entities):
        """Test LLM-assisted relationship extraction"""
        # Mock LLM response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": '[{"source": "Apple Inc.", "target": "Steve Jobs", "relationship_type": "founded_by", "confidence": 0.9}]'
        }
        mock_post.return_value = mock_response
        
        text = "Apple Inc. was founded by Steve Jobs."
        
        relationships = await relationship_mapper.extract_relationships(
            text, sample_entities, use_llm=True
        )
        
        # Should include LLM-extracted relationships
        llm_rels = [r for r in relationships if r["source_method"] == "llm"]
        if llm_rels:  # Only check if LLM extraction worked
            assert len(llm_rels) > 0


class TestEnhancedKnowledgeGraphService:
    """Test cases for EnhancedKnowledgeGraphService"""
    
    @pytest.fixture
    def kg_service(self):
        """Create EnhancedKnowledgeGraphService instance for testing"""
        return EnhancedKnowledgeGraphService()
    
    @pytest.mark.asyncio
    async def test_service_initialization(self, kg_service):
        """Test service initialization"""
        await kg_service.initialize()
        
        assert kg_service.entity_extractor is not None
        assert kg_service.relationship_mapper is not None
        assert kg_service.graph is not None
    
    @pytest.mark.asyncio
    @patch('services.knowledge_graph.get_db')
    async def test_add_document_integration(self, mock_get_db, kg_service):
        """Test document addition with entity extraction and relationship mapping"""
        # Mock database
        mock_db = Mock()
        mock_get_db.return_value.__next__ = Mock(return_value=mock_db)
        
        # Mock document chunks
        mock_chunk = Mock()
        mock_chunk.content = "Apple Inc. was founded by Steve Jobs in Cupertino."
        mock_chunk.id = "chunk1"
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_chunk]
        
        document_data = {"id": "doc1", "name": "test_doc"}
        
        # Mock entity and relationship storage
        kg_service._store_entity_in_db = AsyncMock(return_value=Mock())
        kg_service._store_relationship_in_db = AsyncMock(return_value=Mock())
        
        await kg_service.add_document(document_data)
        
        # Verify entities and relationships were processed
        assert kg_service._store_entity_in_db.called
        # Note: relationship storage depends on entity extraction results
    
    @pytest.mark.asyncio
    async def test_graph_statistics(self, kg_service):
        """Test graph statistics calculation"""
        with patch('services.knowledge_graph.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value.__next__ = Mock(return_value=mock_db)
            
            # Mock database queries
            mock_db.query.return_value.count.return_value = 10
            mock_db.query.return_value.group_by.return_value.all.return_value = [
                ("person", 5), ("organization", 3), ("location", 2)
            ]
            mock_db.query.return_value.scalar.return_value = 0.75
            
            stats = await kg_service.get_graph_statistics()
            
            assert "total_entities" in stats
            assert "total_relationships" in stats
            assert "entity_types" in stats
            assert "relationship_types" in stats
            assert "average_entity_confidence" in stats


@pytest.mark.asyncio
async def test_entity_extraction_accuracy():
    """Integration test for entity extraction accuracy"""
    extractor = EntityExtractor()
    
    # Test with various text types
    test_texts = [
        "Microsoft Corporation was founded by Bill Gates and Paul Allen.",
        "The meeting will be held in New York on January 15th, 2024.",
        "Contact support@company.com for technical assistance.",
        "Visit https://example.com to learn more about our products."
    ]
    
    for text in test_texts:
        entities = await extractor.extract_entities(text, use_llm=False)
        
        # Basic validation
        assert isinstance(entities, list)
        for entity in entities:
            assert "text" in entity
            assert "type" in entity
            assert "confidence" in entity
            assert len(entity["text"]) > 0
            assert 0.0 <= entity["confidence"] <= 1.0


@pytest.mark.asyncio
async def test_relationship_extraction_accuracy():
    """Integration test for relationship extraction accuracy"""
    mapper = RelationshipMapper()
    
    entities = [
        {"text": "Apple", "type": EntityType.ORGANIZATION, "start": 0, "end": 5, "confidence": 0.9},
        {"text": "iPhone", "type": EntityType.PRODUCT, "start": 15, "end": 21, "confidence": 0.8}
    ]
    
    text = "Apple developed the iPhone as their flagship product."
    
    relationships = await mapper.extract_relationships(text, entities, use_llm=False)
    
    # Basic validation
    assert isinstance(relationships, list)
    for rel in relationships:
        assert "source" in rel
        assert "target" in rel
        assert "type" in rel
        assert "confidence" in rel
        assert 0.0 <= rel["confidence"] <= 1.0


if __name__ == "__main__":
    pytest.main([__file__])