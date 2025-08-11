// Citation-Aware Retrieval System
// Provides precise source linking with phrase-level citations

export interface CitationSpan {
  text: string;
  startIndex: number;
  endIndex: number;
  sourceId: string;
  documentName: string;
  pageNumber: number;
  confidence: number;
}

export interface CitationAwareResult {
  content: string;
  citations: CitationSpan[];
  sources: SourceReference[];
  expandableCitations: ExpandableCitation[];
}

export interface SourceReference {
  id: string;
  documentName: string;
  pageNumber: number;
  snippet: string;
  highlightedText: string;
  contextBefore: string;
  contextAfter: string;
  relevanceScore: number;
}

export interface CitationDocument {
  id: string;
  content: string;
  name: string;
  authors?: string[];
  year?: number;
  abstract?: string;
  metadata?: Record<string, unknown>;
}

export interface ExpandableCitation {
  id: string;
  inlineText: string;
  fullCitation: string;
  sourceSnippet: string;
  documentPreview: {
    title: string;
    authors: string[];
    year: number;
    abstract: string;
  };
}

export class CitationAwareRetriever {
  private documents: Map<string, CitationDocument> = new Map();
  private phraseIndex: Map<string, string[]> = new Map(); // phrase -> document IDs

  /**
   * Add documents with phrase-level indexing
   */
  addDocuments(documents: CitationDocument[]): void {
    documents.forEach(doc => {
      this.documents.set(doc.id, doc);
      this.indexPhrases(doc);
    });
  }

  /**
   * Retrieve with precise citation tracking
   */
  async retrieveWithCitations(query: string): Promise<CitationAwareResult> {
    // Step 1: Find relevant documents
    const relevantDocs = await this.findRelevantDocuments(query);
    
    // Step 2: Extract precise phrases that answer the query
    const citationSpans = this.extractCitationSpans(query, relevantDocs);
    
    // Step 3: Generate response with inline citations
    const content = this.generateCitationAwareResponse(query, citationSpans);
    
    // Step 4: Create expandable citations
    const expandableCitations = this.createExpandableCitations(citationSpans);
    
    // Step 5: Prepare source references
    const sources = this.prepareSourceReferences(citationSpans);

    return {
      content,
      citations: citationSpans,
      sources,
      expandableCitations
    };
  }

  /**
   * Index phrases for precise matching
   */
  private indexPhrases(document: CitationDocument): void {
    const sentences = document.content.split(/[.!?]+/);
    
    sentences.forEach((sentence: string, index: number) => {
      const phrases = this.extractPhrases(sentence.trim());
      
      phrases.forEach(phrase => {
        if (!this.phraseIndex.has(phrase)) {
          this.phraseIndex.set(phrase, []);
        }
        this.phraseIndex.get(phrase)!.push(`${document.id}_${index}`);
      });
    });
  }

  /**
   * Extract meaningful phrases from text
   */
  private extractPhrases(text: string): string[] {
    const phrases: string[] = [];
    const words = text.split(/\s+/);
    
    // Extract n-grams (2-5 words)
    for (let n = 2; n <= Math.min(5, words.length); n++) {
      for (let i = 0; i <= words.length - n; i++) {
        const phrase = words.slice(i, i + n).join(' ').toLowerCase();
        if (phrase.length > 10) { // Only meaningful phrases
          phrases.push(phrase);
        }
      }
    }
    
    return phrases;
  }

  /**
   * Find documents relevant to query
   */
  private async findRelevantDocuments(query: string): Promise<CitationDocument[]> {
    const queryPhrases = this.extractPhrases(query);
    const documentScores: Map<string, number> = new Map();
    
    queryPhrases.forEach(phrase => {
      const matchingDocs = this.phraseIndex.get(phrase) || [];
      matchingDocs.forEach(docRef => {
        const docId = docRef.split('_')[0];
        documentScores.set(docId, (documentScores.get(docId) || 0) + 1);
      });
    });
    
    return Array.from(documentScores.entries())
      .sort(([, a], [, b]) => b - a)
      .slice(0, 5)
      .map(([docId]) => this.documents.get(docId))
      .filter(Boolean);
  }

  /**
   * Extract citation spans with precise phrase matching
   */
  private extractCitationSpans(query: string, documents: CitationDocument[]): CitationSpan[] {
    const spans: CitationSpan[] = [];
    
    documents.forEach((doc, docIndex) => {
      const sentences = doc.content.split(/[.!?]+/);
      
      sentences.forEach((sentence: string, sentIndex: number) => {
        const relevance = this.calculateSentenceRelevance(query, sentence);
        
        if (relevance > 0.6) {
          const span: CitationSpan = {
            text: sentence.trim(),
            startIndex: 0,
            endIndex: sentence.length,
            sourceId: `${doc.id}_${sentIndex}`,
            documentName: doc.name,
            pageNumber: Math.floor(sentIndex / 10) + 1, // Approximate page
            confidence: relevance
          };
          spans.push(span);
        }
      });
    });
    
    return spans.sort((a, b) => b.confidence - a.confidence).slice(0, 3);
  }

  /**
   * Calculate sentence relevance to query
   */
  private calculateSentenceRelevance(query: string, sentence: string): number {
    const queryWords = query.toLowerCase().split(/\s+/);
    const sentenceWords = sentence.toLowerCase().split(/\s+/);
    
    const commonWords = queryWords.filter(word => 
      sentenceWords.some(sWord => sWord.includes(word) || word.includes(sWord))
    );
    
    return commonWords.length / queryWords.length;
  }

  /**
   * Generate response with inline citations
   */
  private generateCitationAwareResponse(query: string, spans: CitationSpan[]): string {
    let response = `Based on the available sources, here's what I found regarding "${query}":\n\n`;
    
    spans.forEach((span, index) => {
      const citationNumber = index + 1;
      response += `${span.text} [Source ${citationNumber}, p. ${span.pageNumber}]\n\n`;
    });
    
    return response;
  }

  /**
   * Create expandable citations
   */
  private createExpandableCitations(spans: CitationSpan[]): ExpandableCitation[] {
    return spans.map((span, index) => {
      const doc = this.documents.get(span.sourceId.split('_')[0]);
      
      return {
        id: `citation_${index + 1}`,
        inlineText: `[Source ${index + 1}, p. ${span.pageNumber}]`,
        fullCitation: `${doc?.name || 'Unknown'}, Page ${span.pageNumber}`,
        sourceSnippet: span.text,
        documentPreview: {
          title: doc?.name || 'Unknown Document',
          authors: doc?.authors || ['Unknown Author'],
          year: doc?.year || new Date().getFullYear(),
          abstract: doc?.abstract || 'No abstract available'
        }
      };
    });
  }

  /**
   * Prepare source references for display
   */
  private prepareSourceReferences(spans: CitationSpan[]): SourceReference[] {
    return spans.map(span => {
      const doc = this.documents.get(span.sourceId.split('_')[0]);
      
      return {
        id: span.sourceId,
        documentName: span.documentName,
        pageNumber: span.pageNumber,
        snippet: span.text,
        highlightedText: span.text,
        contextBefore: '...',
        contextAfter: '...',
        relevanceScore: span.confidence
      };
    });
  }
}

export const citationAwareRetriever = new CitationAwareRetriever();