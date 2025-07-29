// Advanced Query Understanding & Intent Recognition
// Implements sophisticated query analysis and expansion

export interface QueryIntent {
  type: 'factual' | 'analytical' | 'comparative' | 'procedural' | 'exploratory' | 'summarization';
  confidence: number;
  entities: string[];
  keywords: string[];
  context: string[];
  temporalAspects: string[];
  scope: 'specific' | 'broad' | 'comprehensive';
}

export interface ExpandedQuery {
  original: string;
  expanded: string[];
  synonyms: string[];
  relatedTerms: string[];
  contextualQueries: string[];
  intent: QueryIntent;
}

export interface RetrievalStrategy {
  type: 'semantic' | 'keyword' | 'hybrid' | 'graph_traversal';
  weights: {
    semantic: number;
    keyword: number;
    temporal: number;
    hierarchical: number;
  };
  filters: {
    documentTypes?: string[];
    timeRange?: { start?: Date; end?: Date };
    importance?: number;
    entities?: string[];
  };
}

export class IntentRecognizer {
  private intentPatterns: Map<QueryIntent['type'], RegExp[]> = new Map();
  private synonymMap: Map<string, string[]> = new Map();
  private contextualTerms: Map<string, string[]> = new Map();

  constructor() {
    this.initializePatterns();
    this.initializeSynonyms();
    this.initializeContextualTerms();
  }

  /**
   * Analyze query and determine intent
   */
  analyzeQuery(query: string): QueryIntent {
    const normalizedQuery = query.toLowerCase().trim();
    const words = normalizedQuery.split(/\s+/);
    
    // Detect intent type
    const intentType = this.detectIntentType(normalizedQuery);
    
    // Extract entities and keywords
    const entities = this.extractQueryEntities(query);
    const keywords = this.extractQueryKeywords(normalizedQuery);
    
    // Detect temporal aspects
    const temporalAspects = this.extractTemporalAspects(normalizedQuery);
    
    // Determine scope
    const scope = this.determineScope(normalizedQuery, words.length);
    
    // Calculate confidence
    const confidence = this.calculateIntentConfidence(intentType, normalizedQuery);

    return {
      type: intentType,
      confidence,
      entities,
      keywords,
      context: this.extractContext(normalizedQuery),
      temporalAspects,
      scope
    };
  }

  /**
   * Expand query with synonyms and related terms
   */
  expandQuery(query: string, intent: QueryIntent): ExpandedQuery {
    const expanded: string[] = [query];
    const synonyms: string[] = [];
    const relatedTerms: string[] = [];
    const contextualQueries: string[] = [];

    // Add synonyms
    intent.keywords.forEach(keyword => {
      const keywordSynonyms = this.synonymMap.get(keyword) || [];
      synonyms.push(...keywordSynonyms);
      
      // Create expanded queries with synonyms
      keywordSynonyms.forEach(synonym => {
        expanded.push(query.replace(new RegExp(keyword, 'gi'), synonym));
      });
    });

    // Add related terms
    intent.keywords.forEach(keyword => {
      const related = this.contextualTerms.get(keyword) || [];
      relatedTerms.push(...related);
    });

    // Generate contextual queries based on intent
    contextualQueries.push(...this.generateContextualQueries(query, intent));

    return {
      original: query,
      expanded: [...new Set(expanded)],
      synonyms: [...new Set(synonyms)],
      relatedTerms: [...new Set(relatedTerms)],
      contextualQueries,
      intent
    };
  }

  /**
   * Determine optimal retrieval strategy
   */
  determineRetrievalStrategy(expandedQuery: ExpandedQuery): RetrievalStrategy {
    const { intent } = expandedQuery;
    
    let strategy: RetrievalStrategy = {
      type: 'hybrid',
      weights: {
        semantic: 0.6,
        keyword: 0.3,
        temporal: 0.05,
        hierarchical: 0.05
      },
      filters: {}
    };

    // Adjust strategy based on intent type
    switch (intent.type) {
      case 'factual':
        strategy.weights.keyword = 0.5;
        strategy.weights.semantic = 0.4;
        strategy.type = 'keyword';
        break;
        
      case 'analytical':
        strategy.weights.semantic = 0.7;
        strategy.weights.hierarchical = 0.2;
        strategy.type = 'semantic';
        break;
        
      case 'comparative':
        strategy.weights.semantic = 0.6;
        strategy.weights.keyword = 0.3;
        strategy.type = 'hybrid';
        break;
        
      case 'procedural':
        strategy.weights.hierarchical = 0.4;
        strategy.weights.semantic = 0.4;
        strategy.weights.keyword = 0.2;
        break;
        
      case 'exploratory':
        strategy.type = 'graph_traversal';
        strategy.weights.semantic = 0.5;
        strategy.weights.hierarchical = 0.3;
        break;
        
      case 'summarization':
        strategy.weights.hierarchical = 0.5;
        strategy.weights.semantic = 0.4;
        strategy.filters.importance = 0.7;
        break;
    }

    // Adjust based on scope
    if (intent.scope === 'comprehensive') {
      strategy.weights.hierarchical += 0.1;
      strategy.weights.semantic += 0.1;
    } else if (intent.scope === 'specific') {
      strategy.weights.keyword += 0.2;
    }

    // Add entity filters
    if (intent.entities.length > 0) {
      strategy.filters.entities = intent.entities;
    }

    return strategy;
  }

  /**
   * Generate contextual search queries
   */
  generateContextualQueries(originalQuery: string, intent: QueryIntent): string[] {
    const contextualQueries: string[] = [];
    
    // Generate queries based on intent type
    switch (intent.type) {
      case 'factual':
        contextualQueries.push(
          `What is ${originalQuery}?`,
          `Define ${originalQuery}`,
          `${originalQuery} definition`
        );
        break;
        
      case 'analytical':
        contextualQueries.push(
          `Analysis of ${originalQuery}`,
          `${originalQuery} research findings`,
          `Study results ${originalQuery}`
        );
        break;
        
      case 'comparative':
        contextualQueries.push(
          `Compare ${originalQuery}`,
          `${originalQuery} vs alternatives`,
          `Differences in ${originalQuery}`
        );
        break;
        
      case 'procedural':
        contextualQueries.push(
          `How to ${originalQuery}`,
          `Steps for ${originalQuery}`,
          `${originalQuery} methodology`
        );
        break;
        
      case 'exploratory':
        contextualQueries.push(
          `Related to ${originalQuery}`,
          `${originalQuery} connections`,
          `Associated with ${originalQuery}`
        );
        break;
        
      case 'summarization':
        contextualQueries.push(
          `Summary of ${originalQuery}`,
          `${originalQuery} overview`,
          `Key points ${originalQuery}`
        );
        break;
    }

    // Add entity-based contextual queries
    intent.entities.forEach(entity => {
      contextualQueries.push(
        `${entity} and ${originalQuery}`,
        `${originalQuery} related to ${entity}`
      );
    });

    return contextualQueries.slice(0, 5); // Limit to 5 contextual queries
  }

  private initializePatterns(): void {
    this.intentPatterns.set('factual', [
      /^what is\b/i,
      /^define\b/i,
      /^who is\b/i,
      /^where is\b/i,
      /^when did\b/i,
      /\bdefinition\b/i,
      /\bexplain\b/i
    ]);

    this.intentPatterns.set('analytical', [
      /\banalyze\b/i,
      /\banalysis\b/i,
      /\bresearch\b/i,
      /\bstudy\b/i,
      /\bfindings\b/i,
      /\bresults\b/i,
      /\bconclusion\b/i,
      /\bimpact\b/i,
      /\beffect\b/i
    ]);

    this.intentPatterns.set('comparative', [
      /\bcompare\b/i,
      /\bcomparison\b/i,
      /\bdifference\b/i,
      /\bsimilar\b/i,
      /\bvs\b/i,
      /\bversus\b/i,
      /\bbetter\b/i,
      /\bworse\b/i,
      /\balternative\b/i
    ]);

    this.intentPatterns.set('procedural', [
      /^how to\b/i,
      /^how do\b/i,
      /\bsteps\b/i,
      /\bprocess\b/i,
      /\bmethod\b/i,
      /\bprocedure\b/i,
      /\bapproach\b/i,
      /\btechnique\b/i
    ]);

    this.intentPatterns.set('exploratory', [
      /\brelated\b/i,
      /\bconnection\b/i,
      /\bassociated\b/i,
      /\blinked\b/i,
      /\bexplore\b/i,
      /\bdiscover\b/i,
      /\bfind\b/i,
      /\bsearch\b/i
    ]);

    this.intentPatterns.set('summarization', [
      /\bsummary\b/i,
      /\bsummarize\b/i,
      /\boverview\b/i,
      /\bmain points\b/i,
      /\bkey findings\b/i,
      /\bhighlights\b/i,
      /\babstract\b/i
    ]);
  }

  private initializeSynonyms(): void {
    this.synonymMap.set('research', ['study', 'investigation', 'analysis', 'examination']);
    this.synonymMap.set('method', ['approach', 'technique', 'procedure', 'methodology']);
    this.synonymMap.set('result', ['finding', 'outcome', 'conclusion', 'discovery']);
    this.synonymMap.set('analysis', ['examination', 'evaluation', 'assessment', 'review']);
    this.synonymMap.set('important', ['significant', 'crucial', 'critical', 'essential']);
    this.synonymMap.set('show', ['demonstrate', 'indicate', 'reveal', 'display']);
    this.synonymMap.set('improve', ['enhance', 'better', 'optimize', 'upgrade']);
    this.synonymMap.set('problem', ['issue', 'challenge', 'difficulty', 'concern']);
  }

  private initializeContextualTerms(): void {
    this.contextualTerms.set('machine learning', ['artificial intelligence', 'neural networks', 'deep learning', 'algorithms']);
    this.contextualTerms.set('research', ['methodology', 'data collection', 'analysis', 'findings']);
    this.contextualTerms.set('analysis', ['statistics', 'interpretation', 'results', 'conclusions']);
    this.contextualTerms.set('study', ['participants', 'methodology', 'results', 'limitations']);
  }

  private detectIntentType(query: string): QueryIntent['type'] {
    let maxScore = 0;
    let detectedIntent: QueryIntent['type'] = 'exploratory';

    this.intentPatterns.forEach((patterns, intentType) => {
      let score = 0;
      patterns.forEach(pattern => {
        if (pattern.test(query)) {
          score += 1;
        }
      });
      
      if (score > maxScore) {
        maxScore = score;
        detectedIntent = intentType;
      }
    });

    return detectedIntent;
  }

  private extractQueryEntities(query: string): string[] {
    const entities: string[] = [];
    
    // Extract capitalized words (potential proper nouns)
    const capitalizedWords = query.match(/\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b/g) || [];
    entities.push(...capitalizedWords);

    // Extract quoted phrases
    const quotedPhrases = query.match(/"([^"]+)"/g) || [];
    entities.push(...quotedPhrases.map(phrase => phrase.replace(/"/g, '')));

    return [...new Set(entities)];
  }

  private extractQueryKeywords(query: string): string[] {
    const stopWords = new Set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'what', 'how', 'when', 'where', 'why', 'who']);
    
    return query
      .toLowerCase()
      .replace(/[^\w\s]/g, '')
      .split(/\s+/)
      .filter(word => word.length > 2 && !stopWords.has(word));
  }

  private extractTemporalAspects(query: string): string[] {
    const temporal: string[] = [];
    
    // Time-related patterns
    const timePatterns = [
      /\b(?:recent|latest|current|new|old|past|future|today|yesterday|tomorrow)\b/gi,
      /\b(?:2020|2021|2022|2023|2024|2025)\b/g,
      /\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\b/gi,
      /\b(?:before|after|during|since|until)\b/gi
    ];

    timePatterns.forEach(pattern => {
      const matches = query.match(pattern) || [];
      temporal.push(...matches.map(m => m.toLowerCase()));
    });

    return [...new Set(temporal)];
  }

  private extractContext(query: string): string[] {
    const context: string[] = [];
    
    // Extract context clues
    const contextPatterns = [
      /\bin the context of\b/gi,
      /\bregarding\b/gi,
      /\bconcerning\b/gi,
      /\babout\b/gi,
      /\brelated to\b/gi
    ];

    contextPatterns.forEach(pattern => {
      if (pattern.test(query)) {
        context.push('contextual');
      }
    });

    return context;
  }

  private determineScope(query: string, wordCount: number): QueryIntent['scope'] {
    // Scope indicators
    const specificIndicators = ['specific', 'exact', 'particular', 'precise'];
    const broadIndicators = ['general', 'overall', 'broad', 'comprehensive'];
    
    const hasSpecific = specificIndicators.some(indicator => 
      query.includes(indicator)
    );
    const hasBroad = broadIndicators.some(indicator => 
      query.includes(indicator)
    );

    if (hasSpecific || wordCount <= 3) return 'specific';
    if (hasBroad || wordCount > 10) return 'comprehensive';
    return 'broad';
  }

  private calculateIntentConfidence(intentType: QueryIntent['type'], query: string): number {
    const patterns = this.intentPatterns.get(intentType) || [];
    let confidence = 0.3; // Base confidence
    
    patterns.forEach(pattern => {
      if (pattern.test(query)) {
        confidence += 0.2;
      }
    });

    // Boost confidence for clear intent indicators
    const strongIndicators = {
      factual: ['what is', 'define', 'definition'],
      analytical: ['analyze', 'research', 'study'],
      comparative: ['compare', 'vs', 'difference'],
      procedural: ['how to', 'steps', 'method'],
      exploratory: ['explore', 'find', 'discover'],
      summarization: ['summary', 'overview', 'main points']
    };

    const indicators = strongIndicators[intentType] || [];
    indicators.forEach(indicator => {
      if (query.toLowerCase().includes(indicator)) {
        confidence += 0.15;
      }
    });

    return Math.min(confidence, 1.0);
  }
}

export const intentRecognizer = new IntentRecognizer();