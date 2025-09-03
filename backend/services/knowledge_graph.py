"""
Knowledge Graph Builder for AI Scholar
Dynamic knowledge graph construction and research connection discovery
"""
import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from datetime import datetime
import networkx as nx
import numpy as np
from collections import defaultdict, Counter
import re
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

@dataclass
class Entity:
    """Knowledge graph entity"""
    id: str
    name: str
    type: str  # person, concept, method, dataset, etc.
    properties: Dict[str, Any]
    confidence: float
    source_documents: List[str]

@dataclass
class Relationship:
    """Knowledge graph relationship"""
    id: str
    source_entity: str
    target_entity: str
    relationship_type: str  # cites, uses, extends, contradicts, etc.
    properties: Dict[str, Any]
    confidence: float
    evidence: List[str]

@dataclass
class ResearchConnection:
    """Discovered research connection"""
    connection_id: str
    entities: List[str]
    connection_type: str
    strength: float
    explanation: str
    supporting_evidence: List[str]
    potential_impact: str

class EntityExtractor:
    """Extract entities from research documents"""
    
    def __init__(self):
        # Load spaCy model for NER
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not found. Using mock entity extraction.")
            self.nlp = None
        
        # Research-specific entity patterns
        self.research_patterns = {
            "methods": [
                r"\b(machine learning|deep learning|neural network|SVM|random forest|regression|clustering)\b",
                r"\b(BERT|GPT|transformer|CNN|RNN|LSTM|GAN)\b",
                r"\b(cross-validation|bootstrap|ANOVA|t-test|chi-square)\b"
            ],
            "datasets": [
                r"\b(ImageNet|MNIST|CIFAR|CoNLL|SQuAD|GLUE|SuperGLUE)\b",
                r"\b([A-Z][a-z]+ dataset|[A-Z][a-z]+ corpus)\b"
            ],
            "metrics": [
                r"\b(accuracy|precision|recall|F1|AUC|BLEU|ROUGE|perplexity)\b",
                r"\b(mean squared error|cross-entropy|IoU|mAP)\b"
            ],
            "concepts": [
                r"\b(artificial intelligence|natural language processing|computer vision)\b",
                r"\b(supervised learning|unsupervised learning|reinforcement learning)\b",
                r"\b(attention mechanism|transfer learning|few-shot learning)\b"
            ]
        }
    
    async def extract_entities(self, text: str, document_id: str) -> List[Entity]:
        """Extract entities from research text"""
        entities = []
        
        # Extract using spaCy NER
        if self.nlp:
            entities.extend(await self._extract_with_spacy(text, document_id))
        
        # Extract research-specific entities
        entities.extend(await self._extract_research_entities(text, document_id))
        
        # Extract author names and citations
        entities.extend(await self._extract_authors_and_citations(text, document_id))
        
        # Deduplicate entities
        entities = self._deduplicate_entities(entities)
        
        return entities
    
    async def _extract_with_spacy(self, text: str, document_id: str) -> List[Entity]:
        """Extract entities using spaCy NER"""
        entities = []
        
        doc = self.nlp(text)
        
        for ent in doc.ents:
            if ent.label_ in ["PERSON", "ORG", "GPE", "PRODUCT", "EVENT"]:
                entity = Entity(
                    id=f"ent_{hash(ent.text.lower()) % 100000}",
                    name=ent.text,
                    type=ent.label_.lower(),
                    properties={
                        "start_char": ent.start_char,
                        "end_char": ent.end_char,
                        "context": text[max(0, ent.start_char-50):ent.end_char+50]
                    },
                    confidence=0.8,  # spaCy confidence
                    source_documents=[document_id]
                )
                entities.append(entity)
        
        return entities
    
    async def _extract_research_entities(self, text: str, document_id: str) -> List[Entity]:
        """Extract research-specific entities using patterns"""
        entities = []
        
        for entity_type, patterns in self.research_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                
                for match in matches:
                    entity_name = match.group().strip()
                    
                    entity = Entity(
                        id=f"res_{hash(entity_name.lower()) % 100000}",
                        name=entity_name,
                        type=entity_type,
                        properties={
                            "pattern_matched": pattern,
                            "start_char": match.start(),
                            "end_char": match.end(),
                            "context": text[max(0, match.start()-50):match.end()+50]
                        },
                        confidence=0.9,  # High confidence for pattern matches
                        source_documents=[document_id]
                    )
                    entities.append(entity)
        
        return entities
    
    async def _extract_authors_and_citations(self, text: str, document_id: str) -> List[Entity]:
        """Extract author names and citations"""
        entities = []
        
        # Extract author patterns
        author_patterns = [
            r"\b([A-Z][a-z]+ et al\.)",  # "Smith et al."
            r"\b([A-Z][a-z]+, [A-Z]\.)",  # "Smith, J."
            r"\b([A-Z][a-z]+ and [A-Z][a-z]+)",  # "Smith and Jones"
        ]
        
        for pattern in author_patterns:
            matches = re.finditer(pattern, text)
            
            for match in matches:
                author_name = match.group(1).strip()
                
                entity = Entity(
                    id=f"auth_{hash(author_name.lower()) % 100000}",
                    name=author_name,
                    type="author",
                    properties={
                        "citation_format": True,
                        "start_char": match.start(),
                        "end_char": match.end()
                    },
                    confidence=0.85,
                    source_documents=[document_id]
                )
                entities.append(entity)
        
        return entities
    
    def _deduplicate_entities(self, entities: List[Entity]) -> List[Entity]:
        """Remove duplicate entities"""
        seen = {}
        deduplicated = []
        
        for entity in entities:
            # Create a key based on normalized name and type
            key = (entity.name.lower().strip(), entity.type)
            
            if key not in seen:
                seen[key] = entity
                deduplicated.append(entity)
            else:
                # Merge source documents
                existing = seen[key]
                existing.source_documents.extend(entity.source_documents)
                existing.source_documents = list(set(existing.source_documents))
                
                # Update confidence (take maximum)
                existing.confidence = max(existing.confidence, entity.confidence)
        
        return deduplicated

class RelationshipExtractor:
    """Extract relationships between entities"""
    
    def __init__(self):
        self.relationship_patterns = {
            "cites": [
                r"(.*?)\s+(cites?|references?|mentions?)\s+(.*?)",
                r"(.*?)\s+(according to|as shown by|demonstrated by)\s+(.*?)"
            ],
            "uses": [
                r"(.*?)\s+(uses?|utilizes?|employs?|applies?)\s+(.*?)",
                r"(.*?)\s+(based on|built on|extends?)\s+(.*?)"
            ],
            "improves": [
                r"(.*?)\s+(improves?|enhances?|outperforms?)\s+(.*?)",
                r"(.*?)\s+(better than|superior to|exceeds?)\s+(.*?)"
            ],
            "contradicts": [
                r"(.*?)\s+(contradicts?|disputes?|challenges?)\s+(.*?)",
                r"(.*?)\s+(unlike|contrary to|different from)\s+(.*?)"
            ]
        }
    
    async def extract_relationships(
        self, 
        text: str, 
        entities: List[Entity], 
        document_id: str
    ) -> List[Relationship]:
        """Extract relationships between entities"""
        relationships = []
        
        # Extract pattern-based relationships
        relationships.extend(
            await self._extract_pattern_relationships(text, entities, document_id)
        )
        
        # Extract co-occurrence relationships
        relationships.extend(
            await self._extract_cooccurrence_relationships(text, entities, document_id)
        )
        
        # Extract citation relationships
        relationships.extend(
            await self._extract_citation_relationships(text, entities, document_id)
        )
        
        return relationships
    
    async def _extract_pattern_relationships(
        self, 
        text: str, 
        entities: List[Entity], 
        document_id: str
    ) -> List[Relationship]:
        """Extract relationships using linguistic patterns"""
        relationships = []
        
        # Create entity name to entity mapping
        entity_map = {entity.name.lower(): entity for entity in entities}
        
        for rel_type, patterns in self.relationship_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                
                for match in matches:
                    source_text = match.group(1).strip()
                    target_text = match.group(3).strip() if len(match.groups()) >= 3 else ""
                    
                    # Find matching entities
                    source_entity = self._find_matching_entity(source_text, entity_map)
                    target_entity = self._find_matching_entity(target_text, entity_map)
                    
                    if source_entity and target_entity:
                        relationship = Relationship(
                            id=f"rel_{hash(f'{source_entity.id}_{target_entity.id}_{rel_type}') % 100000}",
                            source_entity=source_entity.id,
                            target_entity=target_entity.id,
                            relationship_type=rel_type,
                            properties={
                                "pattern_matched": pattern,
                                "context": match.group(0),
                                "start_char": match.start(),
                                "end_char": match.end()
                            },
                            confidence=0.8,
                            evidence=[match.group(0)]
                        )
                        relationships.append(relationship)
        
        return relationships
    
    def _find_matching_entity(self, text: str, entity_map: Dict[str, Entity]) -> Optional[Entity]:
        """Find entity that matches the given text"""
        text_lower = text.lower().strip()
        
        # Exact match
        if text_lower in entity_map:
            return entity_map[text_lower]
        
        # Partial match
        for entity_name, entity in entity_map.items():
            if entity_name in text_lower or text_lower in entity_name:
                return entity
        
        return None
    
    async def _extract_cooccurrence_relationships(
        self, 
        text: str, 
        entities: List[Entity], 
        document_id: str
    ) -> List[Relationship]:
        """Extract relationships based on entity co-occurrence"""
        relationships = []
        
        # Split text into sentences
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            # Find entities in this sentence
            sentence_entities = []
            for entity in entities:
                if entity.name.lower() in sentence.lower():
                    sentence_entities.append(entity)
            
            # Create co-occurrence relationships
            for i, entity1 in enumerate(sentence_entities):
                for entity2 in sentence_entities[i+1:]:
                    relationship = Relationship(
                        id=f"cooc_{hash(f'{entity1.id}_{entity2.id}') % 100000}",
                        source_entity=entity1.id,
                        target_entity=entity2.id,
                        relationship_type="co_occurs",
                        properties={
                            "sentence": sentence.strip(),
                            "co_occurrence_count": 1
                        },
                        confidence=0.6,  # Lower confidence for co-occurrence
                        evidence=[sentence.strip()]
                    )
                    relationships.append(relationship)
        
        return relationships
    
    async def _extract_citation_relationships(
        self, 
        text: str, 
        entities: List[Entity], 
        document_id: str
    ) -> List[Relationship]:
        """Extract citation relationships"""
        relationships = []
        
        # Find citation patterns
        citation_pattern = r'\[(\d+(?:,\s*\d+)*)\]'
        citations = re.finditer(citation_pattern, text)
        
        for citation in citations:
            # Get context around citation
            start = max(0, citation.start() - 100)
            end = min(len(text), citation.end() + 100)
            context = text[start:end]
            
            # Find entities in citation context
            context_entities = []
            for entity in entities:
                if entity.name.lower() in context.lower():
                    context_entities.append(entity)
            
            # Create citation relationships
            for entity in context_entities:
                relationship = Relationship(
                    id=f"cite_{hash(f'{entity.id}_{citation.group()}') % 100000}",
                    source_entity=entity.id,
                    target_entity=f"ref_{citation.group(1)}",
                    relationship_type="cites",
                    properties={
                        "citation_numbers": citation.group(1),
                        "context": context
                    },
                    confidence=0.9,
                    evidence=[context]
                )
                relationships.append(relationship)
        
        return relationships

class KnowledgeGraphBuilder:
    """Build and manage knowledge graphs from research documents"""
    
    def __init__(self):
        self.entity_extractor = EntityExtractor()
        self.relationship_extractor = RelationshipExtractor()
        self.graph = nx.MultiDiGraph()
        self.entities = {}
        self.relationships = {}
    
    async def build_research_ontology(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build knowledge graph from research documents"""
        
        logger.info(f"🔨 Building knowledge graph from {len(documents)} documents...")
        
        all_entities = []
        all_relationships = []
        
        # Process each document
        for doc in documents:
            doc_id = doc.get("id", f"doc_{hash(doc.get('content', '')) % 10000}")
            content = doc.get("content", "")
            
            # Extract entities
            entities = await self.entity_extractor.extract_entities(content, doc_id)
            all_entities.extend(entities)
            
            # Extract relationships
            relationships = await self.relationship_extractor.extract_relationships(
                content, entities, doc_id
            )
            all_relationships.extend(relationships)
        
        # Build graph
        await self._build_graph(all_entities, all_relationships)
        
        # Analyze graph structure
        analysis = await self._analyze_graph_structure()
        
        logger.info(f"✅ Knowledge graph built: {len(self.entities)} entities, {len(self.relationships)} relationships")
        
        return {
            "entities_count": len(self.entities),
            "relationships_count": len(self.relationships),
            "graph_analysis": analysis,
            "build_timestamp": datetime.now().isoformat()
        }
    
    async def _build_graph(self, entities: List[Entity], relationships: List[Relationship]):
        """Build NetworkX graph from entities and relationships"""
        
        # Add entities to graph and storage
        for entity in entities:
            self.entities[entity.id] = entity
            self.graph.add_node(
                entity.id,
                name=entity.name,
                type=entity.type,
                confidence=entity.confidence,
                **entity.properties
            )
        
        # Add relationships to graph and storage
        for relationship in relationships:
            if (relationship.source_entity in self.entities and 
                relationship.target_entity in self.entities):
                
                self.relationships[relationship.id] = relationship
                self.graph.add_edge(
                    relationship.source_entity,
                    relationship.target_entity,
                    relationship_id=relationship.id,
                    type=relationship.relationship_type,
                    confidence=relationship.confidence,
                    **relationship.properties
                )
    
    async def _analyze_graph_structure(self) -> Dict[str, Any]:
        """Analyze knowledge graph structure"""
        
        if len(self.graph.nodes()) == 0:
            return {"error": "Empty graph"}
        
        # Basic graph metrics
        analysis = {
            "nodes": len(self.graph.nodes()),
            "edges": len(self.graph.edges()),
            "density": nx.density(self.graph),
            "is_connected": nx.is_weakly_connected(self.graph)
        }
        
        # Node degree analysis
        degrees = dict(self.graph.degree())
        if degrees:
            analysis["degree_stats"] = {
                "max_degree": max(degrees.values()),
                "min_degree": min(degrees.values()),
                "avg_degree": sum(degrees.values()) / len(degrees)
            }
        
        # Find central nodes
        try:
            centrality = nx.degree_centrality(self.graph)
            top_central = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:5]
            
            analysis["most_central_entities"] = [
                {
                    "entity_id": entity_id,
                    "name": self.entities[entity_id].name,
                    "centrality": centrality_score
                }
                for entity_id, centrality_score in top_central
                if entity_id in self.entities
            ]
        except:
            analysis["most_central_entities"] = []
        
        # Entity type distribution
        entity_types = Counter(entity.type for entity in self.entities.values())
        analysis["entity_type_distribution"] = dict(entity_types)
        
        # Relationship type distribution
        relationship_types = Counter(rel.relationship_type for rel in self.relationships.values())
        analysis["relationship_type_distribution"] = dict(relationship_types)
        
        return analysis
    
    async def find_research_connections(self, query: str, max_results: int = 10) -> List[ResearchConnection]:
        """Discover hidden connections between research topics"""
        
        # Find entities related to query
        query_entities = await self._find_query_entities(query)
        
        if not query_entities:
            return []
        
        connections = []
        
        # Find paths between query entities and other entities
        for query_entity in query_entities:
            # Find entities within 2-3 hops
            nearby_entities = await self._find_nearby_entities(query_entity.id, max_distance=3)
            
            for target_entity_id in nearby_entities:
                if target_entity_id == query_entity.id:
                    continue
                
                # Find shortest path
                try:
                    path = nx.shortest_path(self.graph, query_entity.id, target_entity_id)
                    
                    if len(path) > 1:  # There's a connection
                        connection = await self._analyze_connection_path(path, query)
                        if connection:
                            connections.append(connection)
                
                except nx.NetworkXNoPath:
                    continue
        
        # Sort by connection strength
        connections.sort(key=lambda x: x.strength, reverse=True)
        
        return connections[:max_results]
    
    async def _find_query_entities(self, query: str) -> List[Entity]:
        """Find entities related to the query"""
        query_lower = query.lower()
        matching_entities = []
        
        for entity in self.entities.values():
            # Exact match
            if query_lower in entity.name.lower():
                matching_entities.append(entity)
            # Partial match in properties
            elif any(query_lower in str(prop).lower() for prop in entity.properties.values()):
                matching_entities.append(entity)
        
        return matching_entities
    
    async def _find_nearby_entities(self, entity_id: str, max_distance: int = 3) -> Set[str]:
        """Find entities within max_distance hops"""
        nearby = set()
        
        try:
            # Use BFS to find entities within distance
            distances = nx.single_source_shortest_path_length(
                self.graph, entity_id, cutoff=max_distance
            )
            nearby.update(distances.keys())
        except:
            pass
        
        return nearby
    
    async def _analyze_connection_path(self, path: List[str], query: str) -> Optional[ResearchConnection]:
        """Analyze a connection path and create ResearchConnection"""
        
        if len(path) < 2:
            return None
        
        # Get entities in path
        path_entities = [self.entities.get(entity_id) for entity_id in path]
        path_entities = [e for e in path_entities if e is not None]
        
        if len(path_entities) < 2:
            return None
        
        # Calculate connection strength based on path length and entity confidence
        base_strength = 1.0 / len(path)  # Shorter paths are stronger
        confidence_boost = sum(entity.confidence for entity in path_entities) / len(path_entities)
        strength = base_strength * confidence_boost
        
        # Generate explanation
        explanation = await self._generate_connection_explanation(path_entities, path)
        
        # Assess potential impact
        impact = await self._assess_connection_impact(path_entities)
        
        return ResearchConnection(
            connection_id=f"conn_{hash('_'.join(path)) % 100000}",
            entities=path,
            connection_type="research_path",
            strength=strength,
            explanation=explanation,
            supporting_evidence=self._gather_supporting_evidence(path),
            potential_impact=impact
        )
    
    async def _generate_connection_explanation(
        self, 
        path_entities: List[Entity], 
        path: List[str]
    ) -> str:
        """Generate human-readable explanation of the connection"""
        
        if len(path_entities) < 2:
            return "No clear connection found."
        
        explanation = f"Connection discovered between {path_entities[0].name} and {path_entities[-1].name}"
        
        if len(path_entities) > 2:
            intermediate = ", ".join(entity.name for entity in path_entities[1:-1])
            explanation += f" through {intermediate}"
        
        explanation += f". This connection suggests potential relationships in research areas involving {path_entities[0].type} and {path_entities[-1].type}."
        
        return explanation
    
    async def _assess_connection_impact(self, path_entities: List[Entity]) -> str:
        """Assess the potential impact of the discovered connection"""
        
        entity_types = [entity.type for entity in path_entities]
        
        if "methods" in entity_types and "datasets" in entity_types:
            return "High - Connection between methods and datasets could lead to new experimental approaches"
        elif "concepts" in entity_types and "methods" in entity_types:
            return "Medium - Theoretical concepts connected to practical methods may inspire new research directions"
        elif "author" in entity_types:
            return "Medium - Author connections may reveal collaboration opportunities or research lineages"
        else:
            return "Low - General connection that may provide contextual insights"
    
    def _gather_supporting_evidence(self, path: List[str]) -> List[str]:
        """Gather supporting evidence for the connection"""
        evidence = []
        
        # Get relationships along the path
        for i in range(len(path) - 1):
            source_id = path[i]
            target_id = path[i + 1]
            
            # Find relationships between these entities
            for rel in self.relationships.values():
                if ((rel.source_entity == source_id and rel.target_entity == target_id) or
                    (rel.source_entity == target_id and rel.target_entity == source_id)):
                    evidence.extend(rel.evidence)
        
        return evidence[:5]  # Limit to top 5 pieces of evidence
    
    async def suggest_research_directions(self, user_interests: List[str]) -> List[Dict[str, Any]]:
        """AI-powered research direction suggestions"""
        
        suggestions = []
        
        for interest in user_interests:
            # Find entities related to this interest
            related_entities = await self._find_query_entities(interest)
            
            if not related_entities:
                continue
            
            # Find underexplored connections
            for entity in related_entities[:3]:  # Top 3 most relevant
                # Find entities that are 2-3 hops away (potential research gaps)
                distant_entities = await self._find_research_gaps(entity.id)
                
                for gap_entity_id in distant_entities[:2]:  # Top 2 gaps
                    gap_entity = self.entities.get(gap_entity_id)
                    if gap_entity:
                        suggestion = {
                            "research_direction": f"Explore connections between {entity.name} and {gap_entity.name}",
                            "rationale": f"Limited research found connecting {entity.type} with {gap_entity.type}",
                            "potential_impact": "Medium-High",
                            "starting_points": [entity.name, gap_entity.name],
                            "suggested_methods": await self._suggest_research_methods(entity, gap_entity)
                        }
                        suggestions.append(suggestion)
        
        return suggestions[:10]  # Top 10 suggestions
    
    async def _find_research_gaps(self, entity_id: str) -> List[str]:
        """Find entities that are connected but underexplored"""
        
        # Find entities at distance 2-3 (connected through intermediaries)
        gaps = []
        
        try:
            # Get all entities within distance 3
            all_reachable = nx.single_source_shortest_path_length(
                self.graph, entity_id, cutoff=3
            )
            
            # Filter for entities at distance 2-3 with few direct connections
            for target_id, distance in all_reachable.items():
                if distance >= 2:
                    # Check if there are few direct relationships
                    direct_connections = len(list(self.graph.neighbors(target_id)))
                    if direct_connections < 3:  # Underconnected
                        gaps.append(target_id)
        
        except:
            pass
        
        return gaps
    
    async def _suggest_research_methods(self, entity1: Entity, entity2: Entity) -> List[str]:
        """Suggest research methods for exploring connection between entities"""
        
        methods = []
        
        # Based on entity types, suggest appropriate methods
        if entity1.type == "concepts" and entity2.type == "methods":
            methods.extend([
                "Theoretical analysis and mathematical modeling",
                "Comparative study of existing approaches",
                "Proof-of-concept implementation"
            ])
        elif entity1.type == "datasets" and entity2.type == "methods":
            methods.extend([
                "Empirical evaluation and benchmarking",
                "Cross-validation studies",
                "Performance analysis across different metrics"
            ])
        elif "author" in [entity1.type, entity2.type]:
            methods.extend([
                "Literature review and citation analysis",
                "Collaboration network analysis",
                "Historical research development tracking"
            ])
        else:
            methods.extend([
                "Systematic literature review",
                "Meta-analysis of existing research",
                "Exploratory data analysis"
            ])
        
        return methods

# Global knowledge graph builder
knowledge_graph_builder = KnowledgeGraphBuilder()

# Convenience functions
async def build_knowledge_graph(documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Build knowledge graph from documents"""
    return await knowledge_graph_builder.build_research_ontology(documents)

async def find_research_connections(query: str) -> List[ResearchConnection]:
    """Find research connections for query"""
    return await knowledge_graph_builder.find_research_connections(query)

async def get_research_suggestions(interests: List[str]) -> List[Dict[str, Any]]:
    """Get AI-powered research direction suggestions"""
    return await knowledge_graph_builder.suggest_research_directions(interests)

if __name__ == "__main__":
    # Example usage
    async def test_knowledge_graph():
        print("🧪 Testing Knowledge Graph Builder...")
        
        # Mock documents
        documents = [
            {
                "id": "doc1",
                "content": "Machine learning algorithms like neural networks and SVM are used for classification tasks. BERT and GPT models have revolutionized natural language processing."
            },
            {
                "id": "doc2", 
                "content": "Deep learning methods outperform traditional approaches on ImageNet dataset. Convolutional neural networks achieve high accuracy in computer vision tasks."
            },
            {
                "id": "doc3",
                "content": "Smith et al. demonstrated that transfer learning improves performance. The study used CIFAR-10 dataset and achieved 95% accuracy."
            }
        ]
        
        # Build knowledge graph
        result = await build_knowledge_graph(documents)
        print(f"✅ Knowledge graph built:")
        print(f"  - Entities: {result['entities_count']}")
        print(f"  - Relationships: {result['relationships_count']}")
        
        # Find research connections
        connections = await find_research_connections("machine learning")
        print(f"✅ Found {len(connections)} research connections")
        
        if connections:
            print(f"  - Top connection: {connections[0].explanation}")
        
        # Get research suggestions
        suggestions = await get_research_suggestions(["neural networks", "computer vision"])
        print(f"✅ Generated {len(suggestions)} research suggestions")
        
        if suggestions:
            print(f"  - Top suggestion: {suggestions[0]['research_direction']}")
    
    asyncio.run(test_knowledge_graph())