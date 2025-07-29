// Streaming LLM Response Service
export interface StreamingConfig {
  model: string;
  temperature: number;
  maxTokens: number;
  stopSequences: string[];
}

export interface StreamChunk {
  id: string;
  content: string;
  isComplete: boolean;
  metadata?: {
    tokenCount: number;
    processingTime: number;
    confidence: number;
  };
}

export class StreamingService {
  private baseUrl: string;
  private defaultConfig: StreamingConfig;

  constructor(baseUrl: string = 'http://localhost:11434') {
    this.baseUrl = baseUrl;
    this.defaultConfig = {
      model: 'mistral',
      temperature: 0.7,
      maxTokens: 2048,
      stopSequences: ['</response>', '[END]']
    };
  }

  /**
   * Stream response from LLM
   */
  async *streamResponse(
    prompt: string,
    config: Partial<StreamingConfig> = {}
  ): AsyncGenerator<StreamChunk, void, unknown> {
    const finalConfig = { ...this.defaultConfig, ...config };
    const startTime = Date.now();
    let tokenCount = 0;
    let accumulatedContent = '';

    try {
      const response = await fetch(`${this.baseUrl}/api/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: finalConfig.model,
          prompt,
          stream: true,
          options: {
            temperature: finalConfig.temperature,
            num_predict: finalConfig.maxTokens,
            stop: finalConfig.stopSequences
          }
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body reader available');
      }

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          // Final chunk
          yield {
            id: `chunk_final_${Date.now()}`,
            content: accumulatedContent,
            isComplete: true,
            metadata: {
              tokenCount,
              processingTime: Date.now() - startTime,
              confidence: this.calculateConfidence(accumulatedContent)
            }
          };
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.trim()) {
            try {
              const data = JSON.parse(line);
              
              if (data.response) {
                tokenCount++;
                accumulatedContent += data.response;
                
                yield {
                  id: `chunk_${tokenCount}_${Date.now()}`,
                  content: data.response,
                  isComplete: false,
                  metadata: {
                    tokenCount,
                    processingTime: Date.now() - startTime,
                    confidence: this.calculateConfidence(accumulatedContent)
                  }
                };
              }

              if (data.done) {
                break;
              }
            } catch (error) {
              console.warn('Failed to parse streaming response:', error);
            }
          }
        }
      }
    } catch (error) {
      console.error('Streaming error:', error);
      yield {
        id: `error_${Date.now()}`,
        content: `Error: ${error.message}`,
        isComplete: true,
        metadata: {
          tokenCount: 0,
          processingTime: Date.now() - startTime,
          confidence: 0
        }
      };
    }
  }

  /**
   * Stream with citation tracking
   */
  async *streamWithCitations(
    prompt: string,
    sources: any[],
    config: Partial<StreamingConfig> = {}
  ): AsyncGenerator<StreamChunk & { citations?: any[] }, void, unknown> {
    const citationPrompt = this.buildCitationPrompt(prompt, sources);
    let currentCitations: any[] = [];
    
    for await (const chunk of this.streamResponse(citationPrompt, config)) {
      // Extract citations from content
      const citations = this.extractCitations(chunk.content, sources);
      if (citations.length > 0) {
        currentCitations = [...currentCitations, ...citations];
      }

      yield {
        ...chunk,
        citations: currentCitations
      };
    }
  }

  /**
   * Stream with real-time evaluation
   */
  async *streamWithEvaluation(
    prompt: string,
    config: Partial<StreamingConfig> = {}
  ): AsyncGenerator<StreamChunk & { evaluation?: any }, void, unknown> {
    let accumulatedContent = '';
    
    for await (const chunk of this.streamResponse(prompt, config)) {
      accumulatedContent += chunk.content;
      
      // Real-time evaluation
      const evaluation = this.evaluateResponse(accumulatedContent, chunk.isComplete);
      
      yield {
        ...chunk,
        evaluation
      };
    }
  }

  /**
   * Build citation-aware prompt
   */
  private buildCitationPrompt(prompt: string, sources: any[]): string {
    let citationPrompt = `Based on the following sources, please answer the question and include citations in the format [Source X]:\n\n`;
    
    sources.forEach((source, index) => {
      citationPrompt += `Source ${index + 1}: ${source.content}\n\n`;
    });
    
    citationPrompt += `Question: ${prompt}\n\n`;
    citationPrompt += `Please provide a comprehensive answer with proper citations:`;
    
    return citationPrompt;
  }

  /**
   * Extract citations from streaming content
   */
  private extractCitations(content: string, sources: any[]): any[] {
    const citations: any[] = [];
    const citationPattern = /\[Source (\d+)\]/g;
    let match;
    
    while ((match = citationPattern.exec(content)) !== null) {
      const sourceIndex = parseInt(match[1]) - 1;
      if (sourceIndex >= 0 && sourceIndex < sources.length) {
        citations.push({
          sourceIndex,
          source: sources[sourceIndex],
          position: match.index
        });
      }
    }
    
    return citations;
  }

  /**
   * Calculate response confidence
   */
  private calculateConfidence(content: string): number {
    let confidence = 0.5; // Base confidence
    
    // Length-based confidence
    if (content.length > 100) confidence += 0.1;
    if (content.length > 300) confidence += 0.1;
    
    // Structure-based confidence
    if (content.includes('.') || content.includes('!') || content.includes('?')) {
      confidence += 0.1;
    }
    
    // Coherence indicators
    const coherenceWords = ['therefore', 'however', 'furthermore', 'in conclusion'];
    coherenceWords.forEach(word => {
      if (content.toLowerCase().includes(word)) confidence += 0.05;
    });
    
    return Math.min(confidence, 1.0);
  }

  /**
   * Real-time response evaluation
   */
  private evaluateResponse(content: string, isComplete: boolean): any {
    return {
      coherence: this.evaluateCoherence(content),
      relevance: this.evaluateRelevance(content),
      completeness: isComplete ? this.evaluateCompleteness(content) : 0,
      factualConsistency: this.evaluateFactualConsistency(content),
      readability: this.evaluateReadability(content)
    };
  }

  /**
   * Evaluate coherence
   */
  private evaluateCoherence(content: string): number {
    const sentences = content.split(/[.!?]+/).filter(s => s.trim().length > 0);
    if (sentences.length < 2) return 0.5;
    
    let coherenceScore = 0.5;
    
    // Check for transition words
    const transitionWords = ['however', 'therefore', 'furthermore', 'moreover', 'consequently'];
    const hasTransitions = transitionWords.some(word => content.toLowerCase().includes(word));
    if (hasTransitions) coherenceScore += 0.2;
    
    // Check for logical flow
    const avgSentenceLength = sentences.reduce((sum, s) => sum + s.length, 0) / sentences.length;
    if (avgSentenceLength > 20 && avgSentenceLength < 100) coherenceScore += 0.2;
    
    return Math.min(coherenceScore, 1.0);
  }

  /**
   * Evaluate relevance
   */
  private evaluateRelevance(content: string): number {
    // Simple relevance check based on content structure
    let relevanceScore = 0.5;
    
    if (content.length > 50) relevanceScore += 0.2;
    if (content.includes('based on') || content.includes('according to')) relevanceScore += 0.2;
    
    return Math.min(relevanceScore, 1.0);
  }

  /**
   * Evaluate completeness
   */
  private evaluateCompleteness(content: string): number {
    let completenessScore = 0.3;
    
    if (content.length > 200) completenessScore += 0.2;
    if (content.length > 500) completenessScore += 0.2;
    
    // Check for conclusion indicators
    const conclusionWords = ['in conclusion', 'therefore', 'finally', 'to summarize'];
    if (conclusionWords.some(word => content.toLowerCase().includes(word))) {
      completenessScore += 0.3;
    }
    
    return Math.min(completenessScore, 1.0);
  }

  /**
   * Evaluate factual consistency
   */
  private evaluateFactualConsistency(content: string): number {
    // Basic consistency check
    let consistencyScore = 0.7; // Assume good consistency by default
    
    // Check for contradictory statements (simplified)
    const contradictionPatterns = [
      { positive: /\bis\s+true\b/gi, negative: /\bis\s+false\b/gi },
      { positive: /\bincreases?\b/gi, negative: /\bdecreases?\b/gi }
    ];
    
    contradictionPatterns.forEach(({ positive, negative }) => {
      if (positive.test(content) && negative.test(content)) {
        consistencyScore -= 0.2;
      }
    });
    
    return Math.max(0, consistencyScore);
  }

  /**
   * Evaluate readability
   */
  private evaluateReadability(content: string): number {
    const sentences = content.split(/[.!?]+/).filter(s => s.trim().length > 0);
    const words = content.split(/\s+/).filter(w => w.length > 0);
    
    if (sentences.length === 0 || words.length === 0) return 0;
    
    const avgWordsPerSentence = words.length / sentences.length;
    const avgCharsPerWord = words.reduce((sum, word) => sum + word.length, 0) / words.length;
    
    let readabilityScore = 0.5;
    
    // Optimal sentence length
    if (avgWordsPerSentence > 10 && avgWordsPerSentence < 25) readabilityScore += 0.2;
    
    // Optimal word length
    if (avgCharsPerWord > 3 && avgCharsPerWord < 7) readabilityScore += 0.2;
    
    return Math.min(readabilityScore, 1.0);
  }
}

export const streamingService = new StreamingService();