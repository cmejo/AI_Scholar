// Knowledge Graph Implementation for RAG
// Creates semantic relationships between document chunks and entities

export interface Entity {
  id: string;
  name: string;
  type: 'person' | 'organization' | 'concept' | 'location' | 'date' | 'topic';
  description?: string;
  aliases: string[];
  confidence: number;
}

export interface Relationship {
  id: string;
  source: string;
  target: string;
  type: 'mentions' | 'related_to' | 'part_of' | 'causes' | 'temporal' | 'spatial';
  weight: number;
  context: string;
  documentId: string;
  chunkId: string;
}

export interface KnowledgeNode {
  id: string;
  entity: Entity;
  connections: Relationship[];
  documentReferences: string[];
  importance: number;
}

interface ChunkMetadata {
  title?: string;
  section?: string;
  page?: number;
  timestamp?: number;
  author?: string;
  tags?: string[];
  [key: string]: unknown;
}

interface DocumentChunk {
  id: string;
  content: string;
  documentId: string;
  metadata: ChunkMetadata;
}

export class KnowledgeGraph {
  private nodes: Map<string, KnowledgeNode> = new Map();
  private relationships: Map<string, Relationship> = new Map();
  private entityIndex: Map<string, string[]> = new Map(); // term -> entity IDs

  /**
   * Extract entities from text using NLP patterns
   */
  extractEntities(text: string, documentId: string, chunkId: string): Entity[] {
    const entities: Entity[] = [];
    
    // Named Entity Recognition patterns
    const patterns = {
      person: /\b[A-Z][a-z]+ [A-Z][a-z]+\b/g,
      organization: /\b[A-Z][A-Za-z]+ (?:Inc|Corp|LLC|Ltd|Company|Organization|Institute|University)\b/g,
      date: /\b(?:\d{1,2}\/\d{1,2}\/\d{4}|\d{4}-\d{2}-\d{2}|(?:January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2},? \d{4})\b/g,
      concept: /\b(?:artificial intelligence|machine learning|deep learning|neural network|algorithm|methodology|framework|approach|technique|strategy)\b/gi,
      location: /\b[A-Z][a-z]+ (?:City|State|Country|University|Hospital|Center|Building)\b/g
    };

    Object.entries(patterns).forEach(([type, pattern]) => {
      const matches = text.match(pattern) || [];
      matches.forEach((match, index) => {
        const entity: Entity = {
          id: `${type}_${documentId}_${chunkId}_${index}`,
          name: match.trim(),
          type: type as Entity['type'],
          aliases: [match.trim().toLowerCase()],
          confidence: this.calculateEntityConfidence(match, type, text)
        };
        entities.push(entity);
      });
    });

    return entities;
  }

  /**
   * Build knowledge graph from document chunks
   */
  async buildGraph(chunks: DocumentChunk[]): Promise<void> {
    // Extract entities from all chunks
    const allEntities: Entity[] = [];
    const chunkEntities: Map<string, Entity[]> = new Map();

    for (const chunk of chunks) {
      const entities = this.extractEntities(chunk.content, chunk.documentId, chunk.id);
      allEntities.push(...entities);
      chunkEntities.set(chunk.id, entities);
    }

    // Merge similar entities
    const mergedEntities = this.mergeEntities(allEntities);

    // Create nodes
    mergedEntities.forEach(entity => {
      const node: KnowledgeNode = {
        id: entity.id,
        entity,
        connections: [],
        documentReferences: [entity.id.split('_')[1]], // Extract document ID
        importance: this.calculateImportance(entity, chunks)
      };
      this.nodes.set(entity.id, node);
      
      // Update entity index
      entity.aliases.forEach(alias => {
        if (!this.entityIndex.has(alias)) {
          this.entityIndex.set(alias, []);
        }
        this.entityIndex.get(alias)!.push(entity.id);
      });
    });

    // Create relationships
    this.createRelationships(chunks, chunkEntities);
  }

  /**
   * Find related entities for query expansion
   */
  findRelatedEntities(query: string, maxDepth: number = 2): Entity[] {
    const queryTerms = query.toLowerCase().split(/\s+/);
    const relatedEntities: Set<string> = new Set();
    const visited: Set<string> = new Set();

    // Find direct matches
    queryTerms.forEach(term => {
      const entityIds = this.entityIndex.get(term) || [];
      entityIds.forEach(id => relatedEntities.add(id));
    });

    // Traverse relationships
    const traverse = (entityId: string, depth: number) => {
      if (depth >= maxDepth || visited.has(entityId)) return;
      visited.add(entityId);

      const node = this.nodes.get(entityId);
      if (!node) return;

      node.connections.forEach(rel => {
        if (rel.weight > 0.5) { // Only strong relationships
          relatedEntities.add(rel.target);
          traverse(rel.target, depth + 1);
        }
      });
    };

    relatedEntities.forEach(id => traverse(id, 0));

    return Array.from(relatedEntities)
      .map(id => this.nodes.get(id)?.entity)
      .filter(Boolean) as Entity[];
  }

  /**
   * Get contextual information for entities
   */
  getEntityContext(entityId: string): {
    entity: Entity;
    relatedEntities: Entity[];
    documentContext: string[];
  } | null {
    const node = this.nodes.get(entityId);
    if (!node) return null;

    const relatedEntities = node.connections
      .filter(rel => rel.weight > 0.3)
      .map(rel => this.nodes.get(rel.target)?.entity)
      .filter(Boolean) as Entity[];

    const documentContext = node.connections
      .map(rel => rel.context)
      .filter(Boolean);

    return {
      entity: node.entity,
      relatedEntities,
      documentContext
    };
  }

  private calculateEntityConfidence(match: string, type: string, context: string): number {
    let confidence = 0.5;
    
    // Boost confidence based on context
    if (context.toLowerCase().includes(match.toLowerCase())) {
      confidence += 0.2;
    }
    
    // Type-specific confidence adjustments
    switch (type) {
      case 'person':
        if (/\b(?:Dr|Prof|Mr|Ms|Mrs)\b/.test(match)) confidence += 0.2;
        break;
      case 'organization':
        if (/\b(?:Inc|Corp|LLC|Ltd)\b/.test(match)) confidence += 0.3;
        break;
      case 'concept':
        if (context.toLowerCase().includes('research') || context.toLowerCase().includes('study')) {
          confidence += 0.2;
        }
        break;
    }

    return Math.min(confidence, 1.0);
  }

  private mergeEntities(entities: Entity[]): Entity[] {
    const merged: Map<string, Entity> = new Map();
    
    entities.forEach(entity => {
      const key = entity.name.toLowerCase();
      if (merged.has(key)) {
        const existing = merged.get(key)!;
        existing.aliases = [...new Set([...existing.aliases, ...entity.aliases])];
        existing.confidence = Math.max(existing.confidence, entity.confidence);
      } else {
        merged.set(key, { ...entity });
      }
    });

    return Array.from(merged.values());
  }

  private calculateImportance(entity: Entity, chunks: DocumentChunk[]): number {
    let importance = entity.confidence;
    
    // Frequency-based importance
    const mentions = chunks.filter(chunk => 
      chunk.content.toLowerCase().includes(entity.name.toLowerCase())
    ).length;
    
    importance += Math.log(mentions + 1) * 0.1;
    
    // Type-based importance
    const typeWeights = {
      concept: 0.3,
      person: 0.2,
      organization: 0.25,
      location: 0.1,
      date: 0.05,
      topic: 0.3
    };
    
    importance += typeWeights[entity.type] || 0.1;
    
    return Math.min(importance, 1.0);
  }

  private createRelationships(
    chunks: DocumentChunk[], 
    chunkEntities: Map<string, Entity[]>
  ): void {
    chunks.forEach(chunk => {
      const entities = chunkEntities.get(chunk.id) || [];
      
      // Create co-occurrence relationships
      for (let i = 0; i < entities.length; i++) {
        for (let j = i + 1; j < entities.length; j++) {
          const relationship: Relationship = {
            id: `rel_${entities[i].id}_${entities[j].id}`,
            source: entities[i].id,
            target: entities[j].id,
            type: 'related_to',
            weight: this.calculateRelationshipWeight(entities[i], entities[j], chunk.content),
            context: chunk.content.substring(0, 200),
            documentId: chunk.documentId,
            chunkId: chunk.id
          };
          
          this.relationships.set(relationship.id, relationship);
          
          // Add to node connections
          const sourceNode = this.nodes.get(entities[i].id);
          const targetNode = this.nodes.get(entities[j].id);
          
          if (sourceNode) sourceNode.connections.push(relationship);
          if (targetNode) {
            const reverseRel = { ...relationship, source: relationship.target, target: relationship.source };
            targetNode.connections.push(reverseRel);
          }
        }
      }
    });
  }

  private calculateRelationshipWeight(entity1: Entity, entity2: Entity, context: string): number {
    let weight = 0.3;
    
    // Distance-based weight (closer entities have stronger relationships)
    const pos1 = context.toLowerCase().indexOf(entity1.name.toLowerCase());
    const pos2 = context.toLowerCase().indexOf(entity2.name.toLowerCase());
    
    if (pos1 !== -1 && pos2 !== -1) {
      const distance = Math.abs(pos1 - pos2);
      weight += Math.max(0, (100 - distance) / 100) * 0.4;
    }
    
    // Type-based relationship strength
    if (entity1.type === 'person' && entity2.type === 'organization') weight += 0.2;
    if (entity1.type === 'concept' && entity2.type === 'concept') weight += 0.3;
    
    return Math.min(weight, 1.0);
  }
}

export const knowledgeGraph = new KnowledgeGraph();