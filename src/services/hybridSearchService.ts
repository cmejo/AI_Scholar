// Hybrid Search Service combining semantic and keyword search
import { HierarchicalChunk } from '../utils/hierarchicalChunking';

export interface SearchResult {
  chunk: HierarchicalChunk;
  semanticScore: number;
  keywordScore: number;
  hybridScore: number;
  explanation: string;
}

export interface SearchConfig {
  semanticWeight: number;
  keywordWeight: number;
  rerank: boolean;
  maxResults: number;
  minScore: number;
}

export class HybridSearchService {
  private chunks: HierarchicalChunk[] = [];
  private keywordIndex: Map<string, Set<string>> = new Map(); // term -> chunk IDs
  private idfScores: Map<string, number> = new Map(); // term -> IDF score

  /**
   * Add chunks to search index
   */
  addChunks(chunks: HierarchicalChunk[]): void {
    this.chunks.push(...chunks);
    this.buildKeywordIndex(chunks);
    this.calculateIDF();
  }

  /**
   * Perform hybrid search
   */
  async search(query: string, config: SearchConfig = {
    semanticWeight: 0.7,
    keywordWeight: 0.3,
    rerank: true,
    maxResults: 10,
    minScore: 0.3
  }): Promise<SearchResult[]> {
    
    // Semantic search
    const semanticResults = await this.semanticSearch(query);
    
    // Keyword search (BM25)
    const keywordResults = this.keywordSearch(query);
    
    // Combine results
    const hybridResults = this.combineResults(
      semanticResults,
      keywordResults,
      config
    );
    
    // Re-rank if enabled
    if (config.rerank) {
      return this.reRankResults(hybridResults, query);
    }
    
    return hybridResults
      .filter(result => result.hybridScore >= config.minScore)
      .slice(0, config.maxResults);
  }

  /**
   * Semantic search using embeddings
   */
  private async semanticSearch(query: string): Promise<Map<string, number>> {
    const queryEmbedding = await this.generateEmbedding(query);
    const results = new Map<string, number>();
    
    for (const chunk of this.chunks) {
      if (chunk.embedding) {
        const similarity = this.cosineSimilarity(queryEmbedding, chunk.embedding);
        results.set(chunk.id, similarity);
      }
    }
    
    return results;
  }

  /**
   * Keyword search using BM25
   */
  private keywordSearch(query: string): Map<string, number> {
    const queryTerms = this.tokenize(query);
    const results = new Map<string, number>();
    
    // BM25 parameters
    const k1 = 1.5;
    const b = 0.75;
    const avgDocLength = this.calculateAverageDocumentLength();
    
    for (const chunk of this.chunks) {
      let score = 0;
      const docLength = this.tokenize(chunk.content).length;
      
      for (const term of queryTerms) {
        const tf = this.getTermFrequency(term, chunk);
        const idf = this.idfScores.get(term) || 0;
        
        // BM25 formula
        const numerator = tf * (k1 + 1);
        const denominator = tf + k1 * (1 - b + b * (docLength / avgDocLength));
        
        score += idf * (numerator / denominator);
      }
      
      results.set(chunk.id, score);
    }
    
    return results;
  }

  /**
   * Combine semantic and keyword results
   */
  private combineResults(
    semanticResults: Map<string, number>,
    keywordResults: Map<string, number>,
    config: SearchConfig
  ): SearchResult[] {
    const combinedResults: SearchResult[] = [];
    const allChunkIds = new Set([
      ...semanticResults.keys(),
      ...keywordResults.keys()
    ]);
    
    for (const chunkId of allChunkIds) {
      const chunk = this.chunks.find(c => c.id === chunkId);
      if (!chunk) continue;
      
      const semanticScore = semanticResults.get(chunkId) || 0;
      const keywordScore = this.normalizeScore(keywordResults.get(chunkId) || 0, keywordResults);
      
      const hybridScore = 
        semanticScore * config.semanticWeight +
        keywordScore * config.keywordWeight;
      
      combinedResults.push({
        chunk,
        semanticScore,
        keywordScore,
        hybridScore,
        explanation: this.generateExplanation(semanticScore, keywordScore, hybridScore)
      });
    }
    
    return combinedResults.sort((a, b) => b.hybridScore - a.hybridScore);
  }

  /**
   * Re-rank results using cross-encoder
   */
  private async reRankResults(results: SearchResult[], query: string): Promise<SearchResult[]> {
    // Mock cross-encoder re-ranking
    // In production, use a cross-encoder model like ms-marco-MiniLM-L-12-v2
    
    const reRankedResults = results.map(result => {
      // Simulate cross-encoder scoring
      const crossEncoderScore = Math.random() * 0.2 + result.hybridScore * 0.8;
      
      return {
        ...result,
        hybridScore: crossEncoderScore,
        explanation: result.explanation + ' (re-ranked)'
      };
    });
    
    return reRankedResults.sort((a, b) => b.hybridScore - a.hybridScore);
  }

  /**
   * Build keyword index for BM25
   */
  private buildKeywordIndex(chunks: HierarchicalChunk[]): void {
    for (const chunk of chunks) {
      const terms = this.tokenize(chunk.content);
      
      for (const term of terms) {
        if (!this.keywordIndex.has(term)) {
          this.keywordIndex.set(term, new Set());
        }
        this.keywordIndex.get(term)!.add(chunk.id);
      }
    }
  }

  /**
   * Calculate IDF scores
   */
  private calculateIDF(): void {
    const totalDocs = this.chunks.length;
    
    for (const [term, chunkIds] of this.keywordIndex.entries()) {
      const docFreq = chunkIds.size;
      const idf = Math.log((totalDocs - docFreq + 0.5) / (docFreq + 0.5));
      this.idfScores.set(term, Math.max(0, idf));
    }
  }

  /**
   * Tokenize text
   */
  private tokenize(text: string): string[] {
    return text
      .toLowerCase()
      .replace(/[^\w\s]/g, '')
      .split(/\s+/)
      .filter(term => term.length > 2);
  }

  /**
   * Get term frequency in document
   */
  private getTermFrequency(term: string, chunk: HierarchicalChunk): number {
    const terms = this.tokenize(chunk.content);
    return terms.filter(t => t === term).length;
  }

  /**
   * Calculate average document length
   */
  private calculateAverageDocumentLength(): number {
    const totalLength = this.chunks.reduce((sum, chunk) => {
      return sum + this.tokenize(chunk.content).length;
    }, 0);
    
    return totalLength / this.chunks.length;
  }

  /**
   * Normalize scores to 0-1 range
   */
  private normalizeScore(score: number, allScores: Map<string, number>): number {
    const scores = Array.from(allScores.values());
    const maxScore = Math.max(...scores);
    const minScore = Math.min(...scores);
    
    if (maxScore === minScore) return 0;
    return (score - minScore) / (maxScore - minScore);
  }

  /**
   * Generate explanation for result
   */
  private generateExplanation(semantic: number, keyword: number, hybrid: number): string {
    const explanations: string[] = [];
    
    if (semantic > 0.7) explanations.push('high semantic similarity');
    if (keyword > 0.7) explanations.push('strong keyword matches');
    if (hybrid > 0.8) explanations.push('excellent overall relevance');
    
    return explanations.length > 0 
      ? `Relevant due to: ${explanations.join(', ')}`
      : 'General content match';
  }

  /**
   * Generate embedding (mock implementation)
   */
  private async generateEmbedding(text: string): Promise<number[]> {
    // Mock embedding generation
    return new Array(384).fill(0).map(() => Math.random());
  }

  /**
   * Calculate cosine similarity
   */
  private cosineSimilarity(a: number[], b: number[]): number {
    const dotProduct = a.reduce((sum, val, i) => sum + val * b[i], 0);
    const normA = Math.sqrt(a.reduce((sum, val) => sum + val * val, 0));
    const normB = Math.sqrt(b.reduce((sum, val) => sum + val * val, 0));
    
    return dotProduct / (normA * normB);
  }
}

export const hybridSearchService = new HybridSearchService();