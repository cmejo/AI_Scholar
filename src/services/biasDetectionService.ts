// Bias Detection and Quality Assurance Service
import { BiasDetectionResult } from '../types';

export class BiasDetectionService {
  private biasPatterns: Map<string, RegExp[]> = new Map();
  private factCheckSources: string[] = [];

  constructor() {
    this.initializeBiasPatterns();
    this.initializeFactCheckSources();
  }

  /**
   * Detect bias in text content
   */
  async detectBias(text: string): Promise<BiasDetectionResult[]> {
    const results: BiasDetectionResult[] = [];
    
    for (const [biasType, patterns] of this.biasPatterns.entries()) {
      for (const pattern of patterns) {
        const matches = text.match(pattern);
        if (matches) {
          results.push({
            detected: true,
            type: biasType as any,
            confidence: this.calculateBiasConfidence(matches, text),
            explanation: this.generateBiasExplanation(biasType, matches),
            suggestions: this.generateBiasSuggestions(biasType, matches)
          });
        }
      }
    }

    return results;
  }

  /**
   * Verify facts against reliable sources
   */
  async verifyFacts(claims: string[]): Promise<{
    claim: string;
    verified: boolean;
    confidence: number;
    sources: string[];
    explanation: string;
  }[]> {
    const results = [];
    
    for (const claim of claims) {
      // Mock fact verification
      const verification = await this.checkFactAgainstSources(claim);
      results.push(verification);
    }
    
    return results;
  }

  /**
   * Assess source credibility
   */
  assessSourceCredibility(source: {
    url?: string;
    author?: string;
    publication?: string;
    date?: Date;
  }): {
    credibilityScore: number;
    factors: string[];
    warnings: string[];
  } {
    let score = 0.5; // Base score
    const factors: string[] = [];
    const warnings: string[] = [];

    // Domain credibility
    if (source.url) {
      const domain = this.extractDomain(source.url);
      const domainScore = this.getDomainCredibility(domain);
      score += domainScore * 0.3;
      
      if (domainScore > 0.7) {
        factors.push('Reputable domain');
      } else if (domainScore < 0.3) {
        warnings.push('Questionable domain credibility');
      }
    }

    // Author credibility
    if (source.author) {
      const authorScore = this.getAuthorCredibility(source.author);
      score += authorScore * 0.2;
      
      if (authorScore > 0.8) {
        factors.push('Recognized expert author');
      }
    }

    // Publication credibility
    if (source.publication) {
      const pubScore = this.getPublicationCredibility(source.publication);
      score += pubScore * 0.3;
      
      if (pubScore > 0.8) {
        factors.push('Reputable publication');
      }
    }

    // Recency
    if (source.date) {
      const daysSince = (Date.now() - source.date.getTime()) / (1000 * 60 * 60 * 24);
      if (daysSince > 365) {
        warnings.push('Information may be outdated');
        score -= 0.1;
      } else if (daysSince < 30) {
        factors.push('Recent information');
        score += 0.1;
      }
    }

    return {
      credibilityScore: Math.max(0, Math.min(1, score)),
      factors,
      warnings
    };
  }

  /**
   * Check logical coherence of response
   */
  checkLogicalCoherence(text: string): {
    coherenceScore: number;
    issues: string[];
    suggestions: string[];
  } {
    const issues: string[] = [];
    const suggestions: string[] = [];
    let score = 0.8; // Base score

    // Check for contradictions
    const contradictions = this.findContradictions(text);
    if (contradictions.length > 0) {
      issues.push(`Found ${contradictions.length} potential contradictions`);
      suggestions.push('Review for conflicting statements');
      score -= contradictions.length * 0.1;
    }

    // Check for logical flow
    const flowScore = this.assessLogicalFlow(text);
    score = (score + flowScore) / 2;

    if (flowScore < 0.6) {
      issues.push('Poor logical flow between ideas');
      suggestions.push('Reorganize content for better logical progression');
    }

    // Check for unsupported claims
    const unsupportedClaims = this.findUnsupportedClaims(text);
    if (unsupportedClaims.length > 0) {
      issues.push(`Found ${unsupportedClaims.length} unsupported claims`);
      suggestions.push('Provide evidence for all claims');
      score -= unsupportedClaims.length * 0.05;
    }

    return {
      coherenceScore: Math.max(0, Math.min(1, score)),
      issues,
      suggestions
    };
  }

  /**
   * Generate quality score for response
   */
  generateQualityScore(response: {
    text: string;
    sources: any[];
    relevance: number;
  }): {
    overallScore: number;
    breakdown: {
      relevance: number;
      accuracy: number;
      completeness: number;
      clarity: number;
      bias: number;
    };
    recommendations: string[];
  } {
    const breakdown = {
      relevance: response.relevance,
      accuracy: this.assessAccuracy(response.text, response.sources),
      completeness: this.assessCompleteness(response.text),
      clarity: this.assessClarity(response.text),
      bias: this.assessBiasScore(response.text)
    };

    const overallScore = Object.values(breakdown).reduce((sum, score) => sum + score, 0) / 5;
    
    const recommendations = this.generateQualityRecommendations(breakdown);

    return {
      overallScore,
      breakdown,
      recommendations
    };
  }

  /**
   * Initialize bias detection patterns
   */
  private initializeBiasPatterns(): void {
    this.biasPatterns.set('gender', [
      /\b(he|she) is (naturally|obviously|clearly) (better|worse) at\b/gi,
      /\b(men|women) are (naturally|inherently|typically)\b/gi,
      /\b(his|her) (emotional|logical) (nature|tendencies)\b/gi
    ]);

    this.biasPatterns.set('racial', [
      /\b(people of|those from) .+ are (known for|typically|usually)\b/gi,
      /\b(cultural|ethnic) (stereotypes|generalizations)\b/gi
    ]);

    this.biasPatterns.set('political', [
      /\b(liberals|conservatives) (always|never|typically) (believe|think|do)\b/gi,
      /\b(left|right)-wing (extremists|radicals)\b/gi
    ]);

    this.biasPatterns.set('cultural', [
      /\b(western|eastern) (values|culture) is (superior|better|more advanced)\b/gi,
      /\b(traditional|modern) (societies|cultures) are (more|less)\b/gi
    ]);
  }

  /**
   * Initialize fact-checking sources
   */
  private initializeFactCheckSources(): void {
    this.factCheckSources = [
      'snopes.com',
      'factcheck.org',
      'politifact.com',
      'reuters.com/fact-check',
      'apnews.com/hub/ap-fact-check'
    ];
  }

  /**
   * Calculate bias confidence
   */
  private calculateBiasConfidence(matches: RegExpMatchArray, text: string): number {
    const matchCount = matches.length;
    const textLength = text.length;
    const density = matchCount / (textLength / 1000); // matches per 1000 characters
    
    return Math.min(0.9, 0.3 + density * 0.6);
  }

  /**
   * Generate bias explanation
   */
  private generateBiasExplanation(biasType: string, matches: RegExpMatchArray): string {
    const explanations = {
      gender: 'Detected potential gender bias in language that may reinforce stereotypes',
      racial: 'Found language that may contain racial generalizations or stereotypes',
      political: 'Identified potentially biased political language or generalizations',
      cultural: 'Detected cultural bias that may favor one culture over another'
    };

    return explanations[biasType as keyof typeof explanations] || 'Potential bias detected in content';
  }

  /**
   * Generate bias suggestions
   */
  private generateBiasSuggestions(biasType: string, matches: RegExpMatchArray): string[] {
    const suggestions = {
      gender: [
        'Use gender-neutral language where possible',
        'Avoid generalizations based on gender',
        'Focus on individual capabilities rather than gender-based assumptions'
      ],
      racial: [
        'Avoid racial generalizations',
        'Use specific, factual information instead of stereotypes',
        'Consider the diversity within racial groups'
      ],
      political: [
        'Present multiple political perspectives',
        'Avoid partisan language',
        'Focus on specific policies rather than broad political labels'
      ],
      cultural: [
        'Acknowledge cultural diversity and complexity',
        'Avoid cultural superiority claims',
        'Present cultural differences neutrally'
      ]
    };

    return suggestions[biasType as keyof typeof suggestions] || ['Review content for potential bias'];
  }

  /**
   * Check fact against sources
   */
  private async checkFactAgainstSources(claim: string): Promise<{
    claim: string;
    verified: boolean;
    confidence: number;
    sources: string[];
    explanation: string;
  }> {
    // Mock fact verification
    const verified = Math.random() > 0.3; // 70% chance of verification
    const confidence = Math.random() * 0.4 + 0.6; // 0.6-1.0 confidence
    
    return {
      claim,
      verified,
      confidence,
      sources: verified ? ['factcheck.org', 'reuters.com'] : [],
      explanation: verified 
        ? 'Claim verified by multiple reliable sources'
        : 'Claim could not be verified or contradicts reliable sources'
    };
  }

  /**
   * Extract domain from URL
   */
  private extractDomain(url: string): string {
    try {
      return new URL(url).hostname;
    } catch {
      return url;
    }
  }

  /**
   * Get domain credibility score
   */
  private getDomainCredibility(domain: string): number {
    const highCredibility = [
      'nature.com', 'science.org', 'nejm.org', 'bmj.com',
      'reuters.com', 'apnews.com', 'bbc.com', 'npr.org',
      'gov', 'edu', 'who.int', 'cdc.gov'
    ];

    const mediumCredibility = [
      'wikipedia.org', 'britannica.com', 'smithsonianmag.com'
    ];

    if (highCredibility.some(trusted => domain.includes(trusted))) {
      return 0.9;
    }
    
    if (mediumCredibility.some(medium => domain.includes(medium))) {
      return 0.7;
    }

    if (domain.endsWith('.gov') || domain.endsWith('.edu')) {
      return 0.85;
    }

    return 0.5; // Default score
  }

  /**
   * Get author credibility score
   */
  private getAuthorCredibility(author: string): number {
    // Mock author credibility assessment
    return Math.random() * 0.4 + 0.6; // 0.6-1.0
  }

  /**
   * Get publication credibility score
   */
  private getPublicationCredibility(publication: string): number {
    const highCredibility = [
      'Nature', 'Science', 'Cell', 'The Lancet', 'NEJM',
      'Reuters', 'AP News', 'BBC', 'NPR', 'The Guardian'
    ];

    if (highCredibility.includes(publication)) {
      return 0.9;
    }

    return Math.random() * 0.4 + 0.5; // 0.5-0.9
  }

  /**
   * Find contradictions in text
   */
  private findContradictions(text: string): string[] {
    const contradictions: string[] = [];
    
    // Simple contradiction detection patterns
    const patterns = [
      { positive: /\bis\s+true\b/gi, negative: /\bis\s+false\b/gi },
      { positive: /\bincreases?\b/gi, negative: /\bdecreases?\b/gi },
      { positive: /\bimproves?\b/gi, negative: /\bworsens?\b/gi }
    ];

    patterns.forEach(({ positive, negative }) => {
      const positiveMatches = text.match(positive);
      const negativeMatches = text.match(negative);
      
      if (positiveMatches && negativeMatches) {
        contradictions.push('Potential contradiction detected');
      }
    });

    return contradictions;
  }

  /**
   * Assess logical flow
   */
  private assessLogicalFlow(text: string): number {
    const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 0);
    let flowScore = 0.8;

    // Check for transition words
    const transitionWords = ['however', 'therefore', 'furthermore', 'moreover', 'consequently'];
    const hasTransitions = transitionWords.some(word => 
      text.toLowerCase().includes(word)
    );

    if (hasTransitions) {
      flowScore += 0.1;
    }

    // Check sentence length variation
    const avgLength = sentences.reduce((sum, s) => sum + s.length, 0) / sentences.length;
    const lengthVariation = sentences.some(s => Math.abs(s.length - avgLength) > avgLength * 0.5);
    
    if (lengthVariation) {
      flowScore += 0.1;
    }

    return Math.min(1, flowScore);
  }

  /**
   * Find unsupported claims
   */
  private findUnsupportedClaims(text: string): string[] {
    const claims: string[] = [];
    
    // Patterns that indicate claims
    const claimPatterns = [
      /studies show that/gi,
      /research indicates/gi,
      /it is proven that/gi,
      /experts agree that/gi
    ];

    claimPatterns.forEach(pattern => {
      const matches = text.match(pattern);
      if (matches) {
        claims.push(...matches);
      }
    });

    return claims;
  }

  /**
   * Assess accuracy based on sources
   */
  private assessAccuracy(text: string, sources: any[]): number {
    let score = 0.7; // Base score
    
    if (sources.length > 0) {
      const avgSourceQuality = sources.reduce((sum, source) => {
        const credibility = this.assessSourceCredibility(source);
        return sum + credibility.credibilityScore;
      }, 0) / sources.length;
      
      score = (score + avgSourceQuality) / 2;
    }

    return score;
  }

  /**
   * Assess completeness
   */
  private assessCompleteness(text: string): number {
    let score = 0.6;
    
    // Check for comprehensive coverage
    if (text.length > 200) score += 0.1;
    if (text.length > 500) score += 0.1;
    
    // Check for examples
    if (/for example|such as|including/gi.test(text)) score += 0.1;
    
    // Check for multiple perspectives
    if (/however|on the other hand|alternatively/gi.test(text)) score += 0.1;
    
    return Math.min(1, score);
  }

  /**
   * Assess clarity
   */
  private assessClarity(text: string): number {
    let score = 0.7;
    
    const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 0);
    const avgSentenceLength = sentences.reduce((sum, s) => sum + s.split(' ').length, 0) / sentences.length;
    
    // Prefer moderate sentence length
    if (avgSentenceLength > 10 && avgSentenceLength < 25) {
      score += 0.2;
    } else if (avgSentenceLength > 30) {
      score -= 0.1;
    }
    
    // Check for jargon
    const jargonWords = ['utilize', 'facilitate', 'implement', 'leverage'];
    const hasJargon = jargonWords.some(word => text.toLowerCase().includes(word));
    if (hasJargon) score -= 0.1;
    
    return Math.max(0, Math.min(1, score));
  }

  /**
   * Assess bias score (higher is better)
   */
  private assessBiasScore(text: string): number {
    // Start with high score, reduce for detected bias
    let score = 0.9;
    
    for (const patterns of this.biasPatterns.values()) {
      for (const pattern of patterns) {
        if (pattern.test(text)) {
          score -= 0.1;
        }
      }
    }
    
    return Math.max(0, score);
  }

  /**
   * Generate quality recommendations
   */
  private generateQualityRecommendations(breakdown: any): string[] {
    const recommendations: string[] = [];
    
    if (breakdown.relevance < 0.7) {
      recommendations.push('Improve relevance to the user query');
    }
    
    if (breakdown.accuracy < 0.7) {
      recommendations.push('Verify facts with reliable sources');
    }
    
    if (breakdown.completeness < 0.7) {
      recommendations.push('Provide more comprehensive coverage');
    }
    
    if (breakdown.clarity < 0.7) {
      recommendations.push('Simplify language and improve readability');
    }
    
    if (breakdown.bias < 0.8) {
      recommendations.push('Review for potential bias and use neutral language');
    }
    
    return recommendations;
  }
}

export const biasDetectionService = new BiasDetectionService();