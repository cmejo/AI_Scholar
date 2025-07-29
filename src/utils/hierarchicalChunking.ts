// Hierarchical Document Chunking for Better Context Preservation
// Implements semantic chunking with overlapping context windows

export interface ChunkMetadata {
  level: number; // 0 = document, 1 = section, 2 = paragraph, 3 = sentence
  parent?: string;
  children: string[];
  semanticType: 'title' | 'header' | 'paragraph' | 'list' | 'table' | 'code' | 'quote';
  importance: number;
  keywords: string[];
  entities: string[];
}

export interface HierarchicalChunk {
  id: string;
  content: string;
  level: number;
  metadata: ChunkMetadata;
  embedding?: number[];
  contextWindow: string; // Includes parent and sibling context
}

export class HierarchicalChunker {
  private maxChunkSize: number;
  private overlapSize: number;
  private minChunkSize: number;

  constructor(
    maxChunkSize: number = 512,
    overlapSize: number = 64,
    minChunkSize: number = 100
  ) {
    this.maxChunkSize = maxChunkSize;
    this.overlapSize = overlapSize;
    this.minChunkSize = minChunkSize;
  }

  /**
   * Process document with hierarchical chunking
   */
  async processDocument(
    content: string,
    documentId: string,
    documentType: 'pdf' | 'txt' | 'md' | 'html' = 'txt'
  ): Promise<HierarchicalChunk[]> {
    // Step 1: Parse document structure
    const structure = this.parseDocumentStructure(content, documentType);
    
    // Step 2: Create hierarchical chunks
    const chunks = this.createHierarchicalChunks(structure, documentId);
    
    // Step 3: Add context windows
    this.addContextWindows(chunks);
    
    // Step 4: Extract semantic information
    await this.enrichWithSemantics(chunks);
    
    return chunks;
  }

  /**
   * Parse document into hierarchical structure
   */
  private parseDocumentStructure(content: string, type: string): DocumentNode {
    const root: DocumentNode = {
      id: 'root',
      content: content,
      type: 'document',
      level: 0,
      children: [],
      metadata: {
        importance: 1.0,
        keywords: [],
        entities: []
      }
    };

    switch (type) {
      case 'md':
        return this.parseMarkdown(content, root);
      case 'html':
        return this.parseHTML(content, root);
      default:
        return this.parseText(content, root);
    }
  }

  /**
   * Parse markdown structure
   */
  private parseMarkdown(content: string, root: DocumentNode): DocumentNode {
    const lines = content.split('\n');
    let currentSection: DocumentNode | null = null;
    let currentParagraph: DocumentNode | null = null;

    lines.forEach((line, index) => {
      const trimmed = line.trim();
      
      if (trimmed.startsWith('#')) {
        // Header
        const level = (trimmed.match(/^#+/) || [''])[0].length;
        const headerText = trimmed.replace(/^#+\s*/, '');
        
        const section: DocumentNode = {
          id: `section_${index}`,
          content: headerText,
          type: 'header',
          level: level,
          children: [],
          parent: root.id,
          metadata: {
            importance: Math.max(0.3, 1.0 - (level - 1) * 0.2),
            keywords: this.extractKeywords(headerText),
            entities: []
          }
        };
        
        root.children.push(section);
        currentSection = section;
        currentParagraph = null;
      } else if (trimmed.length > 0) {
        // Content
        if (!currentParagraph || currentParagraph.content.length > this.maxChunkSize) {
          currentParagraph = {
            id: `para_${index}`,
            content: trimmed,
            type: 'paragraph',
            level: (currentSection?.level || 0) + 1,
            children: [],
            parent: currentSection?.id || root.id,
            metadata: {
              importance: 0.5,
              keywords: this.extractKeywords(trimmed),
              entities: []
            }
          };
          
          if (currentSection) {
            currentSection.children.push(currentParagraph);
          } else {
            root.children.push(currentParagraph);
          }
        } else {
          currentParagraph.content += ' ' + trimmed;
          currentParagraph.metadata.keywords.push(...this.extractKeywords(trimmed));
        }
      }
    });

    return root;
  }

  /**
   * Parse plain text structure
   */
  private parseText(content: string, root: DocumentNode): DocumentNode {
    const paragraphs = content.split(/\n\s*\n/).filter(p => p.trim().length > 0);
    
    paragraphs.forEach((paragraph, index) => {
      const sentences = this.splitIntoSentences(paragraph);
      
      const paraNode: DocumentNode = {
        id: `para_${index}`,
        content: paragraph.trim(),
        type: 'paragraph',
        level: 1,
        children: [],
        parent: root.id,
        metadata: {
          importance: this.calculateParagraphImportance(paragraph),
          keywords: this.extractKeywords(paragraph),
          entities: []
        }
      };

      // Create sentence-level chunks if paragraph is too long
      if (paragraph.length > this.maxChunkSize) {
        sentences.forEach((sentence, sentIndex) => {
          if (sentence.trim().length > this.minChunkSize) {
            const sentNode: DocumentNode = {
              id: `sent_${index}_${sentIndex}`,
              content: sentence.trim(),
              type: 'sentence',
              level: 2,
              children: [],
              parent: paraNode.id,
              metadata: {
                importance: 0.3,
                keywords: this.extractKeywords(sentence),
                entities: []
              }
            };
            paraNode.children.push(sentNode);
          }
        });
      }

      root.children.push(paraNode);
    });

    return root;
  }

  /**
   * Parse HTML structure (simplified)
   */
  private parseHTML(content: string, root: DocumentNode): DocumentNode {
    // Remove HTML tags for now, but preserve structure
    const cleanContent = content.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ');
    return this.parseText(cleanContent, root);
  }

  /**
   * Create hierarchical chunks from document structure
   */
  private createHierarchicalChunks(
    structure: DocumentNode,
    documentId: string
  ): HierarchicalChunk[] {
    const chunks: HierarchicalChunk[] = [];

    const traverse = (node: DocumentNode, path: string[] = []) => {
      const chunkId = `${documentId}_${node.id}`;
      
      const chunk: HierarchicalChunk = {
        id: chunkId,
        content: node.content,
        level: node.level,
        metadata: {
          level: node.level,
          parent: node.parent,
          children: node.children.map(c => `${documentId}_${c.id}`),
          semanticType: this.mapTypeToSemantic(node.type),
          importance: node.metadata.importance,
          keywords: node.metadata.keywords,
          entities: node.metadata.entities
        },
        contextWindow: '' // Will be filled later
      };

      chunks.push(chunk);

      // Recursively process children
      node.children.forEach(child => {
        traverse(child, [...path, node.id]);
      });
    };

    traverse(structure);
    return chunks;
  }

  /**
   * Add context windows to chunks
   */
  private addContextWindows(chunks: HierarchicalChunk[]): void {
    const chunkMap = new Map(chunks.map(c => [c.id, c]));

    chunks.forEach(chunk => {
      let contextWindow = chunk.content;

      // Add parent context
      if (chunk.metadata.parent) {
        const parent = chunkMap.get(chunk.metadata.parent);
        if (parent && parent.content !== chunk.content) {
          contextWindow = `${parent.content}\n\n${contextWindow}`;
        }
      }

      // Add sibling context (limited)
      const siblings = chunks.filter(c => 
        c.metadata.parent === chunk.metadata.parent && 
        c.id !== chunk.id
      );

      if (siblings.length > 0) {
        const siblingContext = siblings
          .slice(0, 2) // Limit to 2 siblings
          .map(s => s.content.substring(0, 100))
          .join(' ... ');
        
        contextWindow += `\n\nRelated: ${siblingContext}`;
      }

      chunk.contextWindow = contextWindow;
    });
  }

  /**
   * Enrich chunks with semantic information
   */
  private async enrichWithSemantics(chunks: HierarchicalChunk[]): Promise<void> {
    for (const chunk of chunks) {
      // Extract entities (simplified)
      chunk.metadata.entities = this.extractEntities(chunk.content);
      
      // Calculate importance based on content
      chunk.metadata.importance = this.calculateSemanticImportance(chunk);
      
      // Enhance keywords
      chunk.metadata.keywords = [
        ...chunk.metadata.keywords,
        ...this.extractSemanticKeywords(chunk.content)
      ];
    }
  }

  /**
   * Extract keywords from text
   */
  private extractKeywords(text: string): string[] {
    const words = text.toLowerCase()
      .replace(/[^\w\s]/g, '')
      .split(/\s+/)
      .filter(word => word.length > 3);

    // Simple frequency-based keyword extraction
    const frequency: { [key: string]: number } = {};
    words.forEach(word => {
      frequency[word] = (frequency[word] || 0) + 1;
    });

    return Object.entries(frequency)
      .filter(([_, count]) => count > 1)
      .sort(([_, a], [__, b]) => b - a)
      .slice(0, 10)
      .map(([word, _]) => word);
  }

  /**
   * Extract entities (simplified NER)
   */
  private extractEntities(text: string): string[] {
    const entities: string[] = [];
    
    // Capitalized words (potential proper nouns)
    const capitalizedWords = text.match(/\b[A-Z][a-z]+\b/g) || [];
    entities.push(...capitalizedWords);

    // Technical terms
    const technicalTerms = text.match(/\b(?:algorithm|model|system|framework|method|approach|technique)\b/gi) || [];
    entities.push(...technicalTerms);

    return [...new Set(entities)];
  }

  /**
   * Calculate semantic importance
   */
  private calculateSemanticImportance(chunk: HierarchicalChunk): number {
    let importance = chunk.metadata.importance;

    // Boost importance for headers
    if (chunk.metadata.semanticType === 'header') {
      importance += 0.3;
    }

    // Boost for keyword density
    const keywordDensity = chunk.metadata.keywords.length / chunk.content.split(' ').length;
    importance += keywordDensity * 0.2;

    // Boost for entity mentions
    importance += chunk.metadata.entities.length * 0.05;

    return Math.min(importance, 1.0);
  }

  /**
   * Extract semantic keywords using patterns
   */
  private extractSemanticKeywords(text: string): string[] {
    const patterns = [
      /\b(?:research|study|analysis|investigation|experiment)\b/gi,
      /\b(?:result|finding|conclusion|outcome|discovery)\b/gi,
      /\b(?:method|approach|technique|strategy|framework)\b/gi,
      /\b(?:significant|important|critical|essential|key)\b/gi
    ];

    const keywords: string[] = [];
    patterns.forEach(pattern => {
      const matches = text.match(pattern) || [];
      keywords.push(...matches.map(m => m.toLowerCase()));
    });

    return [...new Set(keywords)];
  }

  /**
   * Split text into sentences
   */
  private splitIntoSentences(text: string): string[] {
    return text.split(/[.!?]+/).filter(s => s.trim().length > 0);
  }

  /**
   * Calculate paragraph importance
   */
  private calculateParagraphImportance(paragraph: string): number {
    let importance = 0.5;

    // First paragraph is often important
    importance += 0.2;

    // Length-based importance
    const wordCount = paragraph.split(' ').length;
    if (wordCount > 50) importance += 0.1;
    if (wordCount > 100) importance += 0.1;

    // Keyword-based importance
    const importantWords = ['research', 'study', 'analysis', 'result', 'conclusion'];
    const hasImportantWords = importantWords.some(word => 
      paragraph.toLowerCase().includes(word)
    );
    if (hasImportantWords) importance += 0.2;

    return Math.min(importance, 1.0);
  }

  /**
   * Map node type to semantic type
   */
  private mapTypeToSemantic(type: string): ChunkMetadata['semanticType'] {
    const mapping: { [key: string]: ChunkMetadata['semanticType'] } = {
      'document': 'title',
      'header': 'header',
      'paragraph': 'paragraph',
      'sentence': 'paragraph',
      'list': 'list',
      'table': 'table',
      'code': 'code',
      'quote': 'quote'
    };
    return mapping[type] || 'paragraph';
  }
}

interface DocumentNode {
  id: string;
  content: string;
  type: string;
  level: number;
  children: DocumentNode[];
  parent?: string;
  metadata: {
    importance: number;
    keywords: string[];
    entities: string[];
  };
}

export const hierarchicalChunker = new HierarchicalChunker();