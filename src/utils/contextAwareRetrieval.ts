// Context-Aware Retrieval System
// Implements sophisticated retrieval strategies based on query intent and knowledge graph

import { knowledgeGraph, Entity } from './knowledgeGraph';
import { hierarchicalChunker, HierarchicalChunk } from './hierarchicalChunking';
import { intentRecognizer, QueryIntent, RetrievalStrategy, ExpandedQuery } from './intentRecognition';

export interface RetrievalResult {
  chunk: HierarchicalChunk;
  relevanceScore: number;
  contextScore: number;
  semanticScore: number;
  hierarchicalScore: number;
  explanation: string;
}

export interface ContextualResponse {
  results: RetrievalResult[];
  totalResults: number;
  strategy: RetrievalStrategy;
  queryAnalysis: {
    intent: QueryIntent;
    expandedQuery: ExpandedQuery;
    relatedEntities: Entity[];
  };
  contextualInsights: string[];
}

export class ContextAwareRetriever {
  private chunks: HierarchicalChunk[] = [];
  private chunkEmbeddings: Map<string, number[]> = new Map();

  /**
   * Add processed chunks to the retrieval system
   */
  addChunks(chunks: HierarchicalChunk[]): void {
    this.chunks.push(...chunks);
    
    // Generate embeddings for new chunks (mock implementation)
    chunks.forEach(chunk => {
      if (!this.chunkEmbeddings.has(chunk.id)) {
        this.chunkEmbeddings.set(chunk.id, this.generateMockEmbedding(chunk.content));
      }
    });
  }

  /**
   * Perform context-aware retrieval
   */
  async retrieve(query: string, maxResults: number = 10): Promise<ContextualResponse> {
    // Step 1: Analyze query intent
    const intent = intentRecognizer.analyzeQuery(query);
    
    // Step 2: Expand query
    const expandedQuery = intentRecognizer.expandQuery(query, intent);
    
    // Step 3: Determine retrieval strategy
    const strategy = intentRecognizer.determineRetrievalStrategy(expandedQuery);
    
    // Step 4: Find related entities
    const relatedEntities = knowledgeGraph.findRelatedEntities(query, 2);
    
    // Step 5: Perform multi-strategy retrieval
    const results = await this.performRetrieval(expandedQuery, strategy, relatedEntities);
    
    // Step 6: Re-rank and filter results
    const rankedResults = this.reRankResults(results, intent, strategy);
    
    // Step 7: Generate contextual insights
    const contextualInsights = this.generateContextualInsights(rankedResults, intent, relatedEntities);

    return {
      results: rankedResults.slice(0, maxResults),
      totalResults: rankedResults.length,
      strategy,
      queryAnalysis: {
        intent,
        expandedQuery,
        relatedEntities
      },
      contextualInsights
    };
  }

  /**
   * Perform multi-strategy retrieval
   */
  private async performRetrieval(
    expandedQuery: ExpandedQuery,
    strategy: RetrievalStrategy,
    relatedEntities: Entity[]
  ): Promise<RetrievalResult[]> {
    const results: RetrievalResult[] = [];
    
    // Generate query embedding
    const queryEmbedding = this.generateMockEmbedding(expandedQuery.original);
    
    for (const chunk of this.chunks) {
      const chunkEmbedding = this.chunkEmbeddings.get(chunk.id);
      if (!chunkEmbedding) continue;

      // Calculate different similarity scores
      const semanticScore = this.calculateSemanticSimilarity(queryEmbedding, chunkEmbedding);
      const keywordScore = this.calculateKeywordSimilarity(expandedQuery, chunk);
      const hierarchicalScore = this.calculateHierarchicalRelevance(chunk, expandedQuery.intent);
      const contextScore = this.calculateContextualRelevance(chunk, relatedEntities);

      // Apply strategy weights
      const relevanceScore = 
        semanticScore * strategy.weights.semantic +
        keywordScore * strategy.weights.keyword +
        hierarchicalScore * strategy.weights.hierarchical +
        contextScore * strategy.weights.temporal;

      // Apply filters
      if (this.passesFilters(chunk, strategy.filters)) {
        results.push({
          chunk,
          relevanceScore,
          contextScore,
          semanticScore,
          hierarchicalScore,
          explanation: this.generateExplanation(chunk, semanticScore, keywordScore, hierarchicalScore, contextScore)
        });
      }
    }

    return results;
  }

  /**
   * Calculate semantic similarity using cosine similarity
   */
  private calculateSemanticSimilarity(queryEmbedding: number[], chunkEmbedding: number[]): number {
    const dotProduct = queryEmbedding.reduce((sum, val, i) => sum + val * chunkEmbedding[i], 0);
    const queryNorm = Math.sqrt(queryEmbedding.reduce((sum, val) => sum + val * val, 0));
    const chunkNorm = Math.sqrt(chunkEmbedding.reduce((sum, val) => sum + val * val, 0));
    
    return dotProduct / (queryNorm * chunkNorm);
  }

  /**
   * Calculate keyword-based similarity
   */
  private calculateKeywordSimilarity(expandedQuery: ExpandedQuery, chunk: HierarchicalChunk): number {
    const queryTerms = [
      ...expandedQuery.intent.keywords,
      ...expandedQuery.synonyms,
      ...expandedQuery.relatedTerms
    ].map(term => term.toLowerCase());

    const chunkText = chunk.content.toLowerCase();
    const chunkTerms = chunk.metadata.keywords.map(k => k.toLowerCase());

    let matches = 0;
    let totalTerms = queryTerms.length;

    queryTerms.forEach(term => {
      if (chunkText.includes(term) || chunkTerms.includes(term)) {
        matches++;
      }
    });

    return totalTerms > 0 ? matches / totalTerms : 0;
  }

  /**
   * Calculate hierarchical relevance based on chunk level and type
   */
  private calculateHierarchicalRelevance(chunk: HierarchicalChunk, intent: QueryIntent): number {
    let score = 0.5; // Base score

    // Adjust based on intent and chunk type
    switch (intent.type) {
      case 'factual':
        if (chunk.metadata.semanticType === 'header') score += 0.3;
        if (chunk.level <= 2) score += 0.2;
        break;
        
      case 'analytical':
        if (chunk.metadata.semanticType === 'paragraph') score += 0.2;
        if (chunk.metadata.importance > 0.7) score += 0.3;
        break;
        
      case 'summarization':
        if (chunk.metadata.semanticType === 'header') score += 0.4;
        if (chunk.level === 1) score += 0.3;
        break;
        
      case 'procedural':
        if (chunk.metadata.semanticType === 'list') score += 0.3;
        if (chunk.content.includes('step') || chunk.content.includes('method')) score += 0.2;
        break;
    }

    // Boost for high-importance chunks
    score += chunk.metadata.importance * 0.2;

    return Math.min(score, 1.0);
  }

  /**
   * Calculate contextual relevance based on entities and relationships
   */
  private calculateContextualRelevance(chunk: HierarchicalChunk, relatedEntities: Entity[]): number {
    let score = 0;

    // Check for entity mentions in chunk
    relatedEntities.forEach(entity => {
      if (chunk.content.toLowerCase().includes(entity.name.toLowerCase())) {
        score += entity.confidence * 0.3;
      }
      
      entity.aliases.forEach(alias => {
        if (chunk.content.toLowerCase().includes(alias)) {
          score += entity.confidence * 0.2;
        }
      });
    });

    // Check for entity mentions in chunk metadata
    chunk.metadata.entities.forEach(chunkEntity => {
      relatedEntities.forEach(queryEntity => {
        if (chunkEntity.toLowerCase().includes(queryEntity.name.toLowerCase())) {
          score += 0.2;
        }
      });
    });

    return Math.min(score, 1.0);
  }

  /**
   * Check if chunk passes strategy filters
   */
  private passesFilters(chunk: HierarchicalChunk, filters: RetrievalStrategy['filters']): boolean {
    // Importance filter
    if (filters.importance && chunk.metadata.importance < filters.importance) {
      return false;
    }

    // Entity filter
    if (filters.entities && filters.entities.length > 0) {
      const hasEntity = filters.entities.some(entity =>
        chunk.metadata.entities.some(chunkEntity =>
          chunkEntity.toLowerCase().includes(entity.toLowerCase())
        )
      );
      if (!hasEntity) return false;
    }

    return true;
  }

  /**
   * Re-rank results using advanced scoring
   */
  private reRankResults(
    results: RetrievalResult[],
    intent: QueryIntent,
    strategy: RetrievalStrategy
  ): RetrievalResult[] {
    return results
      .sort((a, b) => {
        // Primary sort by relevance score
        if (Math.abs(a.relevanceScore - b.relevanceScore) > 0.1) {
          return b.relevanceScore - a.relevanceScore;
        }
        
        // Secondary sort by importance
        return b.chunk.metadata.importance - a.chunk.metadata.importance;
      })
      .filter(result => result.relevanceScore > 0.3); // Filter low-relevance results
  }

  /**
   * Generate contextual insights
   */
  private generateContextualInsights(
    results: RetrievalResult[],
    intent: QueryIntent,
    relatedEntities: Entity[]
  ): string[] {
    const insights: string[] = [];

    // Intent-based insights
    switch (intent.type) {
      case 'factual':
        insights.push(`Found ${results.length} factual references with high confidence`);
        break;
      case 'analytical':
        insights.push(`Retrieved analytical content from ${new Set(results.map(r => r.chunk.metadata.parent)).size} different sections`);
        break;
      case 'comparative':
        insights.push(`Identified comparative information across multiple document sources`);
        break;
    }

    // Entity-based insights
    if (relatedEntities.length > 0) {
      const topEntities = relatedEntities.slice(0, 3).map(e => e.name).join(', ');
      insights.push(`Related entities found: ${topEntities}`);
    }

    // Coverage insights
    const documentCoverage = new Set(results.map(r => r.chunk.id.split('_')[0])).size;
    insights.push(`Information spans ${documentCoverage} document(s)`);

    // Quality insights
    const highQualityResults = results.filter(r => r.relevanceScore > 0.8).length;
    if (highQualityResults > 0) {
      insights.push(`${highQualityResults} high-confidence matches found`);
    }

    return insights;
  }

  /**
   * Generate explanation for result ranking
   */
  private generateExplanation(
    chunk: HierarchicalChunk,
    semanticScore: number,
    keywordScore: number,
    hierarchicalScore: number,
    contextScore: number
  ): string {
    const explanations: string[] = [];

    if (semanticScore > 0.7) {
      explanations.push('high semantic similarity');
    }
    if (keywordScore > 0.5) {
      explanations.push('strong keyword matches');
    }
    if (hierarchicalScore > 0.6) {
      explanations.push('relevant document structure');
    }
    if (contextScore > 0.4) {
      explanations.push('contextual entity relationships');
    }
    if (chunk.metadata.importance > 0.7) {
      explanations.push('high content importance');
    }

    return explanations.length > 0 
      ? `Relevant due to: ${explanations.join(', ')}`
      : 'General content match';
  }

  /**
   * Generate mock embedding (replace with actual embedding service)
   */
  private generateMockEmbedding(text: string): number[] {
    // This would be replaced with actual embedding generation using Ollama
    const embedding = new Array(384).fill(0);
    
    // Simple hash-based mock embedding
    for (let i = 0; i < text.length && i < 384; i++) {
      embedding[i] = (text.charCodeAt(i) / 255) * 2 - 1;
    }
    
    // Normalize
    const norm = Math.sqrt(embedding.reduce((sum, val) => sum + val * val, 0));
    return embedding.map(val => val / norm);
  }
}

export const contextAwareRetriever = new ContextAwareRetriever();