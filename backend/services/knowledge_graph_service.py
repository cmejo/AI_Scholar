"""
Knowledge Graph Service - API adapter for KnowledgeGraphBuilder
Provides CRUD operations and API-compatible interface
"""
import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from .knowledge_graph import KnowledgeGraphBuilder, Entity, Relationship

logger = logging.getLogger(__name__)

class KnowledgeGraphService:
    """Service layer for knowledge graph operations"""
    
    def __init__(self):
        self.builder = KnowledgeGraphBuilder()
        # In-memory storage for demo purposes
        # In production, this would use a proper database
        self.entities_store = {}
        self.relationships_store = {}
    
    async def create_entity(
        self,
        name: str,
        entity_type: str,
        description: Optional[str] = None,
        importance_score: float = 0.5,
        document_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new knowledge graph entity"""
        
        entity_id = str(uuid.uuid4())
        
        entity = Entity(
            id=entity_id,
            name=name,
            type=entity_type,
            properties={
                "description": description,
                "importance_score": importance_score,
                "document_id": document_id,
                **(metadata or {})
            },
            confidence=importance_score,
            source_documents=[document_id] if document_id else []
        )
        
        # Store entity
        self.entities_store[entity_id] = entity
        self.builder.entities[entity_id] = entity
        
        # Add to graph
        self.builder.graph.add_node(
            entity_id,
            name=name,
            type=entity_type,
            confidence=importance_score,
            **entity.properties
        )
        
        return {
            "id": entity_id,
            "name": name,
            "type": entity_type,
            "description": description,
            "importance_score": importance_score,
            "document_id": document_id,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat()
        }
    
    async def get_entities(
        self,
        entity_type: Optional[str] = None,
        document_id: Optional[str] = None,
        min_importance: float = 0.0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get knowledge graph entities with optional filtering"""
        
        entities = []
        
        for entity in self.entities_store.values():
            # Apply filters
            if entity_type and entity.type != entity_type:
                continue
            
            if document_id and document_id not in entity.source_documents:
                continue
            
            if entity.confidence < min_importance:
                continue
            
            entities.append({
                "id": entity.id,
                "name": entity.name,
                "type": entity.type,
                "description": entity.properties.get("description"),
                "importance_score": entity.confidence,
                "document_id": entity.properties.get("document_id"),
                "metadata": {k: v for k, v in entity.properties.items() 
                           if k not in ["description", "importance_score", "document_id"]},
                "created_at": datetime.now().isoformat()
            })
            
            if len(entities) >= limit:
                break
        
        return entities
    
    async def create_relationship(
        self,
        source_entity_id: str,
        target_entity_id: str,
        relationship_type: str,
        confidence_score: float = 0.5,
        context: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new knowledge graph relationship"""
        
        # Validate entities exist
        if source_entity_id not in self.entities_store:
            raise ValueError(f"Source entity {source_entity_id} not found")
        
        if target_entity_id not in self.entities_store:
            raise ValueError(f"Target entity {target_entity_id} not found")
        
        relationship_id = str(uuid.uuid4())
        
        relationship = Relationship(
            id=relationship_id,
            source_entity=source_entity_id,
            target_entity=target_entity_id,
            relationship_type=relationship_type,
            properties={
                "context": context,
                **(metadata or {})
            },
            confidence=confidence_score,
            evidence=[context] if context else []
        )
        
        # Store relationship
        self.relationships_store[relationship_id] = relationship
        self.builder.relationships[relationship_id] = relationship
        
        # Add to graph
        self.builder.graph.add_edge(
            source_entity_id,
            target_entity_id,
            relationship_id=relationship_id,
            type=relationship_type,
            confidence=confidence_score,
            **relationship.properties
        )
        
        return {
            "id": relationship_id,
            "source_entity_id": source_entity_id,
            "target_entity_id": target_entity_id,
            "relationship_type": relationship_type,
            "confidence_score": confidence_score,
            "context": context,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat()
        }
    
    async def query_graph(
        self,
        entity_name: Optional[str] = None,
        relationship_type: Optional[str] = None,
        max_depth: int = 2,
        min_confidence: float = 0.0,
        include_metadata: bool = True
    ) -> Dict[str, Any]:
        """Query the knowledge graph with advanced filtering"""
        
        results = {
            "entities": [],
            "relationships": [],
            "metadata": {}
        }
        
        # Find matching entities
        if entity_name:
            for entity in self.entities_store.values():
                if entity_name.lower() in entity.name.lower():
                    entity_data = {
                        "id": entity.id,
                        "name": entity.name,
                        "type": entity.type,
                        "confidence": entity.confidence
                    }
                    
                    if include_metadata:
                        entity_data["properties"] = entity.properties
                    
                    results["entities"].append(entity_data)
        
        # Find matching relationships
        for relationship in self.relationships_store.values():
            if relationship_type and relationship.relationship_type != relationship_type:
                continue
            
            if relationship.confidence < min_confidence:
                continue
            
            relationship_data = {
                "id": relationship.id,
                "source_entity_id": relationship.source_entity,
                "target_entity_id": relationship.target_entity,
                "relationship_type": relationship.relationship_type,
                "confidence": relationship.confidence
            }
            
            if include_metadata:
                relationship_data["properties"] = relationship.properties
                relationship_data["evidence"] = relationship.evidence
            
            results["relationships"].append(relationship_data)
        
        results["metadata"] = {
            "query_entity": entity_name,
            "query_relationship_type": relationship_type,
            "max_depth": max_depth,
            "min_confidence": min_confidence,
            "total_entities": len(results["entities"]),
            "total_relationships": len(results["relationships"])
        }
        
        return results
    
    async def get_entity_connections(
        self,
        entity_id: str,
        depth: int = 2,
        min_confidence: float = 0.5
    ) -> Dict[str, Any]:
        """Get connections for a specific entity"""
        
        if entity_id not in self.entities_store:
            raise ValueError(f"Entity {entity_id} not found")
        
        connections = []
        
        # Find direct relationships
        for relationship in self.relationships_store.values():
            if relationship.confidence < min_confidence:
                continue
            
            if relationship.source_entity == entity_id:
                target_entity = self.entities_store.get(relationship.target_entity)
                if target_entity:
                    connections.append({
                        "relationship_id": relationship.id,
                        "relationship_type": relationship.relationship_type,
                        "target_entity": {
                            "id": target_entity.id,
                            "name": target_entity.name,
                            "type": target_entity.type
                        },
                        "confidence": relationship.confidence,
                        "direction": "outgoing"
                    })
            
            elif relationship.target_entity == entity_id:
                source_entity = self.entities_store.get(relationship.source_entity)
                if source_entity:
                    connections.append({
                        "relationship_id": relationship.id,
                        "relationship_type": relationship.relationship_type,
                        "source_entity": {
                            "id": source_entity.id,
                            "name": source_entity.name,
                            "type": source_entity.type
                        },
                        "confidence": relationship.confidence,
                        "direction": "incoming"
                    })
        
        return {
            "connections": connections,
            "entity_id": entity_id,
            "depth": depth,
            "min_confidence": min_confidence,
            "total_connections": len(connections)
        }
    
    async def build_from_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build knowledge graph from documents using the underlying builder"""
        
        result = await self.builder.build_research_ontology(documents)
        
        # Sync the built entities and relationships to our stores
        self.entities_store.update(self.builder.entities)
        self.relationships_store.update(self.builder.relationships)
        
        return result
    
    async def find_research_connections(self, query: str, max_results: int = 10):
        """Find research connections using the underlying builder"""
        return await self.builder.find_research_connections(query, max_results)
    
    async def suggest_research_directions(self, user_interests: List[str]):
        """Get research direction suggestions using the underlying builder"""
        return await self.builder.suggest_research_directions(user_interests)