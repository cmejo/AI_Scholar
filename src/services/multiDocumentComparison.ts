// Multi-Document Comparison Service
export interface DocumentComparison {
  documents: string[];
  comparisonType: 'approach' | 'methodology' | 'results' | 'conclusions' | 'general';
  similarities: ComparisonPoint[];
  differences: ComparisonPoint[];
  summary: string;
  detailedAnalysis: ComparisonSection[];
}

export interface ComparisonPoint {
  aspect: string;
  document1: { content: string; source: string; page: number };
  document2: { content: string; source: string; page: number };
  similarity: number;
  explanation: string;
}

export interface ComparisonSection {
  title: string;
  document1Content: string;
  document2Content: string;
  analysis: string;
  significance: 'high' | 'medium' | 'low';
}

export class MultiDocumentComparisonService {
  private documents: Map<string, any> = new Map();

  /**
   * Add documents for comparison
   */
  addDocuments(documents: any[]): void {
    documents.forEach(doc => {
      this.documents.set(doc.id, doc);
    });
  }

  /**
   * Compare multiple documents on specific aspects
   */
  async compareDocuments(
    documentIds: string[],
    query: string,
    comparisonType: DocumentComparison['comparisonType'] = 'general'
  ): Promise<DocumentComparison> {
    
    if (documentIds.length < 2) {
      throw new Error('At least 2 documents required for comparison');
    }

    const docs = documentIds.map(id => this.documents.get(id)).filter(Boolean);
    
    // Extract relevant sections from each document
    const relevantSections = await this.extractRelevantSections(docs, query, comparisonType);
    
    // Perform comparison analysis
    const similarities = this.findSimilarities(relevantSections, comparisonType);
    const differences = this.findDifferences(relevantSections, comparisonType);
    
    // Generate detailed analysis
    const detailedAnalysis = this.generateDetailedAnalysis(relevantSections, comparisonType);
    
    // Create summary
    const summary = this.generateComparisonSummary(similarities, differences, comparisonType);

    return {
      documents: documentIds,
      comparisonType,
      similarities,
      differences,
      summary,
      detailedAnalysis
    };
  }

  /**
   * Side-by-side RAG across selected documents
   */
  async sideBySideRAG(documentIds: string[], query: string): Promise<{
    document1Response: any;
    document2Response: any;
    comparison: DocumentComparison;
  }> {
    if (documentIds.length !== 2) {
      throw new Error('Side-by-side comparison requires exactly 2 documents');
    }

    // Get RAG responses from each document separately
    const doc1Response = await this.getDocumentSpecificResponse(documentIds[0], query);
    const doc2Response = await this.getDocumentSpecificResponse(documentIds[1], query);
    
    // Compare the responses
    const comparison = await this.compareDocuments(documentIds, query);

    return {
      document1Response: doc1Response,
      document2Response: doc2Response,
      comparison
    };
  }

  /**
   * Extract sections relevant to comparison type
   */
  private async extractRelevantSections(
    documents: any[],
    query: string,
    comparisonType: DocumentComparison['comparisonType']
  ): Promise<Map<string, any[]>> {
    const sectionMap = new Map<string, any[]>();
    
    const sectionKeywords = {
      approach: ['approach', 'method', 'strategy', 'technique', 'framework'],
      methodology: ['methodology', 'procedure', 'protocol', 'design', 'implementation'],
      results: ['results', 'findings', 'outcomes', 'data', 'analysis'],
      conclusions: ['conclusion', 'summary', 'implications', 'discussion', 'future work'],
      general: ['introduction', 'background', 'overview', 'abstract']
    };

    const keywords = sectionKeywords[comparisonType] || sectionKeywords.general;
    
    documents.forEach(doc => {
      const sections = this.extractSectionsByKeywords(doc, keywords, query);
      sectionMap.set(doc.id, sections);
    });

    return sectionMap;
  }

  /**
   * Extract sections by keywords
   */
  private extractSectionsByKeywords(document: any, keywords: string[], query: string): any[] {
    const sections: any[] = [];
    const content = document.content.toLowerCase();
    const sentences = document.content.split(/[.!?]+/);
    
    sentences.forEach((sentence: string, index: number) => {
      const lowerSentence = sentence.toLowerCase();
      
      // Check if sentence contains relevant keywords or query terms
      const hasKeywords = keywords.some(keyword => lowerSentence.includes(keyword));
      const hasQueryTerms = query.toLowerCase().split(' ').some(term => 
        lowerSentence.includes(term)
      );
      
      if (hasKeywords || hasQueryTerms) {
        sections.push({
          content: sentence.trim(),
          index,
          relevance: this.calculateRelevance(sentence, keywords, query),
          source: document.name,
          page: Math.floor(index / 10) + 1
        });
      }
    });

    return sections.sort((a, b) => b.relevance - a.relevance).slice(0, 5);
  }

  /**
   * Calculate relevance score
   */
  private calculateRelevance(sentence: string, keywords: string[], query: string): number {
    const lowerSentence = sentence.toLowerCase();
    let score = 0;
    
    // Keyword matching
    keywords.forEach(keyword => {
      if (lowerSentence.includes(keyword)) score += 0.3;
    });
    
    // Query term matching
    query.toLowerCase().split(' ').forEach(term => {
      if (lowerSentence.includes(term)) score += 0.2;
    });
    
    // Length bonus for substantial content
    if (sentence.length > 100) score += 0.1;
    
    return Math.min(score, 1.0);
  }

  /**
   * Find similarities between documents
   */
  private findSimilarities(
    sectionMap: Map<string, any[]>,
    comparisonType: DocumentComparison['comparisonType']
  ): ComparisonPoint[] {
    const similarities: ComparisonPoint[] = [];
    const docIds = Array.from(sectionMap.keys());
    
    if (docIds.length < 2) return similarities;
    
    const doc1Sections = sectionMap.get(docIds[0]) || [];
    const doc2Sections = sectionMap.get(docIds[1]) || [];
    
    doc1Sections.forEach(section1 => {
      doc2Sections.forEach(section2 => {
        const similarity = this.calculateTextSimilarity(section1.content, section2.content);
        
        if (similarity > 0.6) {
          similarities.push({
            aspect: this.extractAspect(section1.content, comparisonType),
            document1: {
              content: section1.content,
              source: section1.source,
              page: section1.page
            },
            document2: {
              content: section2.content,
              source: section2.source,
              page: section2.page
            },
            similarity,
            explanation: `Both documents share similar ${comparisonType} regarding ${this.extractAspect(section1.content, comparisonType)}`
          });
        }
      });
    });
    
    return similarities.sort((a, b) => b.similarity - a.similarity).slice(0, 3);
  }

  /**
   * Find differences between documents
   */
  private findDifferences(
    sectionMap: Map<string, any[]>,
    comparisonType: DocumentComparison['comparisonType']
  ): ComparisonPoint[] {
    const differences: ComparisonPoint[] = [];
    const docIds = Array.from(sectionMap.keys());
    
    if (docIds.length < 2) return differences;
    
    const doc1Sections = sectionMap.get(docIds[0]) || [];
    const doc2Sections = sectionMap.get(docIds[1]) || [];
    
    // Find unique aspects in each document
    doc1Sections.forEach(section1 => {
      const hasMatch = doc2Sections.some(section2 => 
        this.calculateTextSimilarity(section1.content, section2.content) > 0.4
      );
      
      if (!hasMatch) {
        // Find the most contrasting section from doc2
        const mostContrasting = doc2Sections.reduce((best, section2) => {
          const similarity = this.calculateTextSimilarity(section1.content, section2.content);
          return similarity < best.similarity ? { section: section2, similarity } : best;
        }, { section: doc2Sections[0], similarity: 1.0 });
        
        if (mostContrasting.section) {
          differences.push({
            aspect: this.extractAspect(section1.content, comparisonType),
            document1: {
              content: section1.content,
              source: section1.source,
              page: section1.page
            },
            document2: {
              content: mostContrasting.section.content,
              source: mostContrasting.section.source,
              page: mostContrasting.section.page
            },
            similarity: mostContrasting.similarity,
            explanation: `Documents differ in their ${comparisonType} approach to ${this.extractAspect(section1.content, comparisonType)}`
          });
        }
      }
    });
    
    return differences.slice(0, 3);
  }

  /**
   * Calculate text similarity
   */
  private calculateTextSimilarity(text1: string, text2: string): number {
    const words1 = text1.toLowerCase().split(/\s+/);
    const words2 = text2.toLowerCase().split(/\s+/);
    
    const commonWords = words1.filter(word => words2.includes(word));
    const totalWords = new Set([...words1, ...words2]).size;
    
    return commonWords.length / totalWords;
  }

  /**
   * Extract main aspect from content
   */
  private extractAspect(content: string, comparisonType: DocumentComparison['comparisonType']): string {
    const aspectKeywords = {
      approach: ['attention', 'transformer', 'neural', 'algorithm'],
      methodology: ['experiment', 'dataset', 'training', 'evaluation'],
      results: ['accuracy', 'performance', 'improvement', 'score'],
      conclusions: ['implications', 'future', 'limitations', 'significance'],
      general: ['concept', 'idea', 'principle', 'theory']
    };
    
    const keywords = aspectKeywords[comparisonType] || aspectKeywords.general;
    const foundKeyword = keywords.find(keyword => 
      content.toLowerCase().includes(keyword)
    );
    
    return foundKeyword || 'general concept';
  }

  /**
   * Generate detailed analysis
   */
  private generateDetailedAnalysis(
    sectionMap: Map<string, any[]>,
    comparisonType: DocumentComparison['comparisonType']
  ): ComparisonSection[] {
    const analysis: ComparisonSection[] = [];
    const docIds = Array.from(sectionMap.keys());
    
    if (docIds.length < 2) return analysis;
    
    const doc1Sections = sectionMap.get(docIds[0]) || [];
    const doc2Sections = sectionMap.get(docIds[1]) || [];
    
    // Create sections for different aspects
    const aspects = ['main approach', 'key findings', 'methodology'];
    
    aspects.forEach(aspect => {
      const doc1Content = doc1Sections
        .filter(s => s.content.toLowerCase().includes(aspect.split(' ')[0]))
        .map(s => s.content)
        .join(' ') || doc1Sections[0]?.content || '';
      
      const doc2Content = doc2Sections
        .filter(s => s.content.toLowerCase().includes(aspect.split(' ')[0]))
        .map(s => s.content)
        .join(' ') || doc2Sections[0]?.content || '';
      
      if (doc1Content && doc2Content) {
        analysis.push({
          title: `Comparison of ${aspect}`,
          document1Content: doc1Content,
          document2Content: doc2Content,
          analysis: `The documents show ${this.calculateTextSimilarity(doc1Content, doc2Content) > 0.5 ? 'similar' : 'different'} approaches to ${aspect}`,
          significance: this.assessSignificance(doc1Content, doc2Content)
        });
      }
    });
    
    return analysis;
  }

  /**
   * Assess significance of comparison
   */
  private assessSignificance(content1: string, content2: string): 'high' | 'medium' | 'low' {
    const similarity = this.calculateTextSimilarity(content1, content2);
    const avgLength = (content1.length + content2.length) / 2;
    
    if (avgLength > 200 && Math.abs(similarity - 0.5) > 0.3) return 'high';
    if (avgLength > 100 && Math.abs(similarity - 0.5) > 0.2) return 'medium';
    return 'low';
  }

  /**
   * Generate comparison summary
   */
  private generateComparisonSummary(
    similarities: ComparisonPoint[],
    differences: ComparisonPoint[],
    comparisonType: DocumentComparison['comparisonType']
  ): string {
    let summary = `Comparison Analysis (${comparisonType}):\n\n`;
    
    if (similarities.length > 0) {
      summary += `Key Similarities:\n`;
      similarities.forEach((sim, index) => {
        summary += `${index + 1}. ${sim.explanation} (${(sim.similarity * 100).toFixed(0)}% similarity)\n`;
      });
      summary += '\n';
    }
    
    if (differences.length > 0) {
      summary += `Key Differences:\n`;
      differences.forEach((diff, index) => {
        summary += `${index + 1}. ${diff.explanation}\n`;
      });
    }
    
    return summary;
  }

  /**
   * Get document-specific response
   */
  private async getDocumentSpecificResponse(documentId: string, query: string): Promise<any> {
    const document = this.documents.get(documentId);
    if (!document) throw new Error('Document not found');
    
    // Extract relevant content from this specific document
    const relevantContent = this.extractRelevantContent(document, query);
    
    return {
      documentId,
      documentName: document.name,
      response: `Based on ${document.name}: ${relevantContent}`,
      sources: [{
        document: document.name,
        page: 1,
        relevance: 0.9
      }]
    };
  }

  /**
   * Extract relevant content from document
   */
  private extractRelevantContent(document: any, query: string): string {
    const sentences = document.content.split(/[.!?]+/);
    const queryTerms = query.toLowerCase().split(' ');
    
    const relevantSentences = sentences
      .filter((sentence: string) => {
        const lowerSentence = sentence.toLowerCase();
        return queryTerms.some(term => lowerSentence.includes(term));
      })
      .slice(0, 3);
    
    return relevantSentences.join('. ') || 'No directly relevant content found.';
  }
}

export const multiDocumentComparison = new MultiDocumentComparisonService();